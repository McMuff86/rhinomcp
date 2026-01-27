using System;
using System.Collections.Generic;
using System.Linq;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using Rhino;
using Rhino.Commands;
using Rhino.Geometry;
using Rhino.Input;
using Rhino.Input.Custom;
using Rhino.UI;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using static System.Runtime.InteropServices.JavaScript.JSType;
using System.Text.Json;
using Rhino.DocObjects;
using rhinomcp.Serializers;
using JsonException = Newtonsoft.Json.JsonException;
using Eto.Forms;
using RhinoMCPPlugin.Functions;

namespace RhinoMCPPlugin
{
    public class RhinoMCPServer
    {
        private string host;
        private int port;
        private bool running;
        private TcpListener listener;
        private Thread serverThread;
        private readonly object lockObject = new object();
        private RhinoMCPFunctions handler;
        private bool debugMode = true;
        
        // WebSocket server for real-time event streaming
        private RhinoMCPWebSocketServer wsServer;
        private const int DefaultWebSocketPort = 2000;
        
        // Static log buffer for capturing Rhino command line output
        private static readonly Queue<string> _logBuffer = new Queue<string>();
        private static readonly object _logLock = new object();
        private const int MaxLogEntries = 100;
        
        /// <summary>
        /// Add a log entry to the buffer and also write to Rhino command line.
        /// </summary>
        public static void Log(string message)
        {
            lock (_logLock)
            {
                string timestampedMessage = $"[{DateTime.Now:HH:mm:ss.fff}] {message}";
                _logBuffer.Enqueue(timestampedMessage);
                while (_logBuffer.Count > MaxLogEntries)
                {
                    _logBuffer.Dequeue();
                }
            }
            RhinoApp.WriteLine(message);
        }
        
        /// <summary>
        /// Get recent log entries.
        /// </summary>
        public static List<string> GetRecentLogs(int count = 50)
        {
            lock (_logLock)
            {
                return _logBuffer.TakeLast(Math.Min(count, _logBuffer.Count)).ToList();
            }
        }
        
        /// <summary>
        /// Clear the log buffer.
        /// </summary>
        public static void ClearLogs()
        {
            lock (_logLock)
            {
                _logBuffer.Clear();
            }
        }
        

        public RhinoMCPServer(string host = "127.0.0.1", int port = 1999)
        {
            this.host = host;
            this.port = port;
            this.running = false;
            this.listener = null;
            this.serverThread = null;
            this.handler = new RhinoMCPFunctions();
        }

        public void SetDebugMode(bool enable)
        {
            debugMode = enable;
            // Sync with Logger: debug mode = Debug level, otherwise Info
            Logger.CurrentLevel = enable ? LogLevel.Debug : LogLevel.Info;
            Logger.Info($"Debug mode {(enable ? "enabled" : "disabled")} (log level: {Logger.CurrentLevel})");
        }

        public bool GetDebugMode()
        {
            return debugMode;
        }

        /// <summary>
        /// Gets the current server host address.
        /// </summary>
        public string GetHost()
        {
            return host;
        }

        /// <summary>
        /// Gets the current server port.
        /// </summary>
        public int GetPort()
        {
            return port;
        }

        /// <summary>
        /// Returns true if server is bound to 0.0.0.0 (remote access enabled).
        /// </summary>
        public bool IsRemoteAccessEnabled()
        {
            return host == "0.0.0.0";
        }

        public bool IsRunning()
        {
            return running;
        }

        /// <summary>
        /// Gets information about the WebSocket server status.
        /// </summary>
        public (bool IsRunning, string Endpoint, int ClientCount) GetWebSocketStatus()
        {
            if (wsServer != null && wsServer.IsRunning)
            {
                return (true, wsServer.Endpoint, wsServer.ClientCount);
            }
            return (false, null, 0);
        }


        public void Start()
        {
            lock (lockObject)
            {
                if (running)
                {
                    Logger.Warning("Server is already running");
                    return;
                }

                running = true;
            }

            try
            {
                // Create TCP listener
                IPAddress ipAddress = IPAddress.Parse(host);
                listener = new TcpListener(ipAddress, port);
                listener.Start();

                // Start server thread
                serverThread = new Thread(ServerLoop);
                serverThread.IsBackground = true;
                serverThread.Start();

                // Show appropriate server type based on binding
                string serverType = (host == "0.0.0.0") ? "RhinoTCP" : "RhinoMCP";
                Logger.Info($"{serverType} server started on {host}:{port}");
                
                // Start WebSocket server for real-time event streaming
                wsServer = new RhinoMCPWebSocketServer();
                wsServer.Start(host, DefaultWebSocketPort);
                
                // Show tools list at Debug level
                if (Logger.CurrentLevel >= LogLevel.Debug)
                {
                    Logger.Raw("-------------------------------------------");
                    PrintAvailableTools();
                    Logger.Raw("-------------------------------------------");
                }
                
                // Show ready message based on binding
                if (host == "0.0.0.0")
                {
                    Logger.Info("Ready for TCP connections (remote access enabled)");
                }
                else
                {
                    Logger.Info("Ready for MCP connections (localhost only)");
                }
            }
            catch (Exception e)
            {
                Logger.Error("Failed to start server", e);
                Stop();
            }
        }

        /// <summary>
        /// Prints all available MCP tools to the Rhino command line.
        /// </summary>
        private void PrintAvailableTools()
        {
            var tools = GetAvailableTools();
            Logger.Raw($"Available Tools ({tools.Count}):");
            
            // Group tools by category
            var categories = new Dictionary<string, List<string>>
            {
                ["Document"] = new List<string> { "get_document_info", "ping" },
                ["Objects"] = new List<string> { "create_object", "create_objects", "get_object_info", "get_selected_objects_info", "delete_object", "modify_object", "modify_objects", "select_objects" },
                ["Layers"] = new List<string> { "create_layer", "get_or_set_current_layer", "delete_layer" },
                ["Materials"] = new List<string> { "create_material", "assign_material_to_layer" },
                ["Render"] = new List<string> { "set_render_settings", "add_light", "set_camera", "render_view" },
                ["Boolean"] = new List<string> { "boolean_operation" },
                ["Transform"] = new List<string> { "copy_object", "mirror_object", "array_linear", "array_polar" },
                ["Curves"] = new List<string> { "offset_curve", "fillet_curves", "chamfer_curves" },
                ["Surfaces"] = new List<string> { "loft_curves", "extrude_curve", "revolve_curve" },
                ["Scripting"] = new List<string> { "execute_rhinoscript_python_code" },
                ["Debug"] = new List<string> { "set_debug_mode", "log_thought" },
                ["Grasshopper API"] = new List<string> { "load_grasshopper_definition", "set_grasshopper_parameter", "solve_grasshopper", "bake_grasshopper", "get_grasshopper_outputs", "unload_grasshopper_definition", "list_grasshopper_definitions" }
            };

            foreach (var category in categories)
            {
                var availableInCategory = category.Value.Where(t => tools.Contains(t)).ToList();
                if (availableInCategory.Count > 0)
                {
                    Logger.Raw($"  [{category.Key}]: {string.Join(", ", availableInCategory)}");
                }
            }
        }

        /// <summary>
        /// Returns a list of all available MCP tool names.
        /// </summary>
        public List<string> GetAvailableTools()
        {
            return new List<string>
            {
                // Document & System
                "get_document_info",
                "ping",
                "set_debug_mode",
                "log_thought",
                "get_logs",
                "clear_logs",
                "get_command_history",
                // Note: Command monitoring now via WebSocket (port 2000)
                // Objects
                "create_object",
                "create_objects",
                "get_object_info",
                "get_selected_objects_info",
                "delete_object",
                "modify_object",
                "modify_objects",
                "select_objects",
                "get_object_properties",
                "set_object_properties",
                // Layers
                "create_layer",
                "get_or_set_current_layer",
                "delete_layer",
                // Materials
                "create_material",
                "assign_material_to_layer",
                // Boolean Operations
                "boolean_operation",
                // Transform Operations
                "copy_object",
                "mirror_object",
                "array_linear",
                "array_polar",
                // Curve Operations
                "offset_curve",
                "fillet_curves",
                "chamfer_curves",
                // Surface Operations
                "loft_curves",
                "extrude_curve",
                "revolve_curve",
                // Dimension Operations
                "create_linear_dimension",
                "create_angular_dimension",
                "create_radial_dimension",
                // File Operations
                "open_file",
                "save_file",
                "export_file",
                // Viewport Operations
                "set_view",
                "zoom_extents",
                "zoom_selected",
                "capture_viewport",
                // Render Operations
                "set_render_settings",
                "add_light",
                "set_camera",
                "render_view",
                // Scripting
                "execute_rhinoscript_python_code",
                // Grasshopper API (SDK-based)
                "load_grasshopper_definition",
                "set_grasshopper_parameter",
                "solve_grasshopper",
                "bake_grasshopper",
                "get_grasshopper_outputs",
                "unload_grasshopper_definition",
                "list_grasshopper_definitions"
            };
        }

        public void Stop()
        {
            lock (lockObject)
            {
                running = false;
            }

            // Stop WebSocket server
            if (wsServer != null)
            {
                try
                {
                    wsServer.Stop();
                }
                catch
                {
                    // Ignore errors on WebSocket shutdown
                }
                wsServer = null;
            }

            // Close listener
            if (listener != null)
            {
                try
                {
                    listener.Stop();
                }
                catch
                {
                    // Ignore errors on closing
                }
                listener = null;
            }

            // Wait for thread to finish
            if (serverThread != null && serverThread.IsAlive)
            {
                try
                {
                    serverThread.Join(1000); // Wait up to 1 second
                }
                catch
                {
                    // Ignore errors on join
                }
                serverThread = null;
            }

            Logger.Info("Server stopped");
        }

        private void ServerLoop()
        {
            Logger.Debug("Server thread started");

            while (IsRunning())
            {
                try
                {
                    // Set a timeout to check running condition periodically
                    listener.Server.ReceiveTimeout = 1000;
                    listener.Server.SendTimeout = 1000;

                    // Wait for client connection
                    if (listener.Pending())
                    {
                        TcpClient client = listener.AcceptTcpClient();
                        Logger.Debug($"Client connected: {client.Client.RemoteEndPoint}");

                        // Handle client in a separate thread
                        Thread clientThread = new Thread(() => HandleClient(client));
                        clientThread.IsBackground = true;
                        clientThread.Start();
                    }
                    else
                    {
                        // No pending connections, sleep a bit to prevent CPU overuse
                        Thread.Sleep(100);
                    }
                }
                catch (Exception e)
                {
                    Logger.Error($"Error in server loop: {e.Message}");

                    if (!IsRunning())
                        break;

                    Thread.Sleep(500);
                }
            }

            Logger.Debug("Server thread stopped");
        }

        private void HandleClient(TcpClient client)
        {
            Logger.Verbose("Client handler started");

            byte[] buffer = new byte[8192];
            string incompleteData = string.Empty;

            try
            {
                NetworkStream stream = client.GetStream();

                while (IsRunning())
                {
                    try
                    {
                        // Check if there's data available to read
                        if (client.Available > 0 || stream.DataAvailable)
                        {
                            int bytesRead = stream.Read(buffer, 0, buffer.Length);
                            if (bytesRead == 0)
                            {
                                Logger.Debug("Client disconnected");
                                break;
                            }

                            string data = Encoding.UTF8.GetString(buffer, 0, bytesRead);
                            incompleteData += data;

                            try
                            {
                                // Try to parse as JSON
                                JObject command = JObject.Parse(incompleteData);
                                incompleteData = string.Empty;

                                // Use ManualResetEventSlim to wait for UI thread completion
                                using (var completionEvent = new System.Threading.ManualResetEventSlim(false))
                                {
                                    Exception caughtException = null;
                                    
                                    // Execute command on Rhino's main thread
                                    RhinoApp.InvokeOnUiThread(new Action(() =>
                                    {
                                        try
                                        {
                                            JObject response = ExecuteCommand(command);
                                            string responseJson = JsonConvert.SerializeObject(response);

                                            try
                                            {
                                                byte[] responseBytes = Encoding.UTF8.GetBytes(responseJson);
                                                stream.Write(responseBytes, 0, responseBytes.Length);
                                                stream.Flush();
                                            }
                                            catch (Exception sendEx)
                                            {
                                                Logger.Warning($"Failed to send response - client disconnected: {sendEx.Message}");
                                            }
                                        }
                                        catch (Exception e)
                                        {
                                            caughtException = e;
                                            Logger.Error($"Error executing command: {e.Message}");
                                            try
                                            {
                                                string errorCmdType = command["type"]?.ToString() ?? "unknown";
                                                JObject errorResponse = new JObject
                                                {
                                                    ["status"] = "error",
                                                    ["error_code"] = ErrorCode.FromException(e, errorCmdType),
                                                    ["message"] = e.Message
                                                };

                                                byte[] errorBytes = Encoding.UTF8.GetBytes(errorResponse.ToString());
                                                stream.Write(errorBytes, 0, errorBytes.Length);
                                                stream.Flush();
                                            }
                                            catch
                                            {
                                                // Ignore send errors
                                            }
                                        }
                                        finally
                                        {
                                            // Signal completion
                                            completionEvent.Set();
                                        }
                                    }));
                                    
                                    // Wait for UI thread to complete (with timeout)
                                    if (!completionEvent.Wait(TimeSpan.FromSeconds(60)))
                                    {
                                        Logger.Warning("Command execution timed out after 60 seconds");
                                    }
                                }
                            }
                            catch (JsonException)
                            {
                                // Incomplete JSON data, wait for more
                            }
                        }
                        else
                        {
                            // No data available, sleep a bit to prevent CPU overuse
                            Thread.Sleep(50);
                        }
                    }
                    catch (Exception e)
                    {
                        Logger.Error($"Error receiving data: {e.Message}");
                        break;
                    }
                }
            }
            catch (Exception e)
            {
                Logger.Error($"Error in client handler: {e.Message}");
            }
            finally
            {
                try
                {
                    client.Close();
                }
                catch
                {
                    // Ignore errors on close
                }
                Logger.Verbose("Client handler stopped");
            }
        }

        private JObject ExecuteCommand(JObject command)
        {
            // Accept both "type" and "command" keys for compatibility
            string cmdType = command["type"]?.ToString() ?? command["command"]?.ToString();
            JObject parameters = command["params"] as JObject ?? new JObject();

            // Validate cmdType
            if (string.IsNullOrEmpty(cmdType))
            {
                Logger.Error($"Missing or empty command type. Received: {command.ToString()}");
                return new JObject
                {
                    ["status"] = "error",
                    ["message"] = "Missing or empty command type. Expected 'type' or 'command' field.",
                    ["received_keys"] = new JArray(command.Properties().Select(p => p.Name))
                };
            }

            try
            {
                Logger.Debug($"Executing: {cmdType}");
                Logger.Verbose($"Parameters: {parameters.ToString()}");

                JObject result = ExecuteCommandInternal(cmdType, parameters);

                Logger.Debug($"Command {cmdType} completed");
                return result;
            }
            catch (Exception e)
            {
                Logger.Error($"Command {cmdType} failed: {e.Message}");
                Logger.Verbose($"StackTrace: {e.StackTrace}");
                return new JObject
                {
                    ["status"] = "error",
                    ["error_code"] = ErrorCode.RHINO_ERROR,
                    ["message"] = e.Message
                };
            }
        }

        private JObject ExecuteCommandInternal(string cmdType, JObject parameters)
        {

            // Dictionary to map command types to handler methods
            Dictionary<string, Func<JObject, JObject>> handlers = new Dictionary<string, Func<JObject, JObject>>
            {
                ["get_document_info"] = this.handler.GetDocumentInfo,
                ["create_object"] = this.handler.CreateObject,
                ["create_objects"] = this.handler.CreateObjects,
                ["get_object_info"] = this.handler.GetObjectInfo,
                ["get_selected_objects_info"] = this.handler.GetSelectedObjectsInfo,
                ["delete_object"] = this.handler.DeleteObject,
                ["modify_object"] = this.handler.ModifyObject,
                ["modify_objects"] = this.handler.ModifyObjects,
                ["execute_rhinoscript_python_code"] = this.handler.ExecuteRhinoscript,
                ["select_objects"] = this.handler.SelectObjects,
                ["create_layer"] = this.handler.CreateLayer,
                ["get_or_set_current_layer"] = this.handler.GetOrSetCurrentLayer,
                ["delete_layer"] = this.handler.DeleteLayer,
                ["ping"] = this.handler.Ping,
                ["set_debug_mode"] = this.handler.SetDebugMode,
                ["log_thought"] = this.handler.LogThought,
                ["create_material"] = this.handler.CreateMaterial,
                ["assign_material_to_layer"] = this.handler.AssignMaterialToLayer,
                ["boolean_operation"] = this.handler.BooleanOperation,
                ["copy_object"] = this.handler.CopyObject,
                ["mirror_object"] = this.handler.MirrorObject,
                ["array_linear"] = this.handler.ArrayLinear,
                ["array_polar"] = this.handler.ArrayPolar,
                ["offset_curve"] = this.handler.OffsetCurve,
                ["fillet_curves"] = this.handler.FilletCurves,
                ["chamfer_curves"] = this.handler.ChamferCurves,
                ["join_curves"] = this.handler.JoinCurves,
                ["explode_curve"] = this.handler.ExplodeCurve,
                ["loft_curves"] = this.handler.LoftCurves,
                ["extrude_curve"] = this.handler.ExtrudeCurve,
                ["revolve_curve"] = this.handler.RevolveCurve,
                ["create_linear_dimension"] = this.handler.CreateLinearDimension,
                ["create_angular_dimension"] = this.handler.CreateAngularDimension,
                ["create_radial_dimension"] = this.handler.CreateRadialDimension,
                ["get_object_properties"] = this.handler.GetObjectProperties,
                ["set_object_properties"] = this.handler.SetObjectProperties,
                // File Operations
                ["open_file"] = this.handler.OpenFile,
                ["save_file"] = this.handler.SaveFile,
                ["export_file"] = this.handler.ExportFile,
                // Viewport Operations
                ["set_view"] = this.handler.SetView,
                ["zoom_extents"] = this.handler.ZoomExtents,
                ["zoom_selected"] = this.handler.ZoomSelected,
                ["capture_viewport"] = this.handler.CaptureViewport,
                // Render Operations
                ["set_render_settings"] = this.handler.SetRenderSettings,
                ["add_light"] = this.handler.AddLight,
                ["set_camera"] = this.handler.SetCamera,
                ["render_view"] = this.handler.RenderView,
                // Group & Block Operations
                ["create_group"] = this.handler.CreateGroup,
                ["ungroup"] = this.handler.Ungroup,
                ["create_block"] = this.handler.CreateBlock,
                ["insert_block"] = this.handler.InsertBlock,
                ["explode_block"] = this.handler.ExplodeBlock,
                // Mesh Operations
                ["import_mesh"] = this.handler.ImportMesh,
                ["export_mesh"] = this.handler.ExportMesh,
                ["mesh_from_brep"] = this.handler.MeshFromBrep,
                // Grasshopper Operations (GrasshopperPlayer-based)
                ["run_grasshopper"] = this.handler.RunGrasshopper,
                ["generate_bill_of_materials"] = this.handler.GenerateBillOfMaterials,
                // Grasshopper API Operations (SDK-based)
                ["load_grasshopper_definition"] = this.handler.LoadGrasshopperDefinition,
                ["set_grasshopper_parameter"] = this.handler.SetGrasshopperParameter,
                ["solve_grasshopper"] = this.handler.SolveGrasshopper,
                ["bake_grasshopper"] = this.handler.BakeGrasshopper,
                ["get_grasshopper_outputs"] = this.handler.GetGrasshopperOutputs,
                ["unload_grasshopper_definition"] = this.handler.UnloadGrasshopperDefinition,
                ["list_grasshopper_definitions"] = this.handler.ListGrasshopperDefinitions,
                // Async Script Execution (for WebSocket-based control)
                ["start_script_async"] = this.handler.StartScriptAsync,
                ["send_command_input"] = this.handler.SendCommandInput,
                ["get_current_prompt"] = this.handler.GetCurrentPrompt,
                // Command History (for agent communication)
                ["get_command_history"] = this.handler.GetCommandHistory,
                ["get_logs"] = (p) => {
                    int count = p["count"]?.Value<int>() ?? 50;
                    var logs = GetRecentLogs(count);
                    return new JObject
                    {
                        ["logs"] = new JArray(logs),
                        ["count"] = logs.Count
                    };
                },
                ["clear_logs"] = (p) => {
                    ClearLogs();
                    return new JObject { ["message"] = "Logs cleared" };
                }
                // Note: Command line monitoring now uses WebSocket (port 2000)
            };

            if (handlers.TryGetValue(cmdType, out var handler))
            {
                var doc = RhinoDoc.ActiveDoc;
                var record = doc.BeginUndoRecord("Run MCP command");
                try
                {
                    JObject result = handler(parameters);
                    return new JObject
                    {
                        ["status"] = "success",
                        ["result"] = result
                    };
                }
                catch (Exception e)
                {
                    Logger.Error($"Handler error for {cmdType}: {e.Message}");
                    Logger.Verbose($"StackTrace: {e.StackTrace}");
                    return new JObject
                    {
                        ["status"] = "error",
                        ["error_code"] = ErrorCode.FromException(e, cmdType),
                        ["message"] = e.Message
                    };
                }
                finally
                {
                    doc.EndUndoRecord(record);
                }
            }
            else
            {
                return new JObject
                {
                    ["status"] = "error",
                    ["error_code"] = ErrorCode.UNKNOWN_COMMAND,
                    ["message"] = $"Unknown command type: {cmdType}"
                };
            }
        }
    }
}
