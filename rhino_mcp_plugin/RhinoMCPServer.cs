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
            RhinoApp.WriteLine($"Debug mode {(enable ? "enabled" : "disabled")}");
        }

        public bool GetDebugMode()
        {
            return debugMode;
        }

        public bool IsRunning()
        {
            return running;
        }


        public void Start()
        {
            lock (lockObject)
            {
                if (running)
                {
                    RhinoApp.WriteLine("Server is already running");
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

                RhinoApp.WriteLine($"RhinoMCP server started on {host}:{port}");
                RhinoApp.WriteLine("-------------------------------------------");
                PrintAvailableTools();
                RhinoApp.WriteLine("-------------------------------------------");
                RhinoApp.WriteLine("Ready for MCP connections.");
            }
            catch (Exception e)
            {
                RhinoApp.WriteLine($"Failed to start server: {e.Message}");
                Stop();
            }
        }

        /// <summary>
        /// Prints all available MCP tools to the Rhino command line.
        /// </summary>
        private void PrintAvailableTools()
        {
            var tools = GetAvailableTools();
            RhinoApp.WriteLine($"Available MCP Tools ({tools.Count}):");
            
            // Group tools by category
            var categories = new Dictionary<string, List<string>>
            {
                ["Document"] = new List<string> { "get_document_info", "ping" },
                ["Objects"] = new List<string> { "create_object", "create_objects", "get_object_info", "get_selected_objects_info", "delete_object", "modify_object", "modify_objects", "select_objects" },
                ["Layers"] = new List<string> { "create_layer", "get_or_set_current_layer", "delete_layer" },
                ["Materials"] = new List<string> { "create_material", "assign_material_to_layer" },
                ["Boolean"] = new List<string> { "boolean_operation" },
                ["Transform"] = new List<string> { "copy_object", "mirror_object", "array_linear", "array_polar" },
                ["Curves"] = new List<string> { "offset_curve", "fillet_curves", "chamfer_curves" },
                ["Surfaces"] = new List<string> { "loft_curves", "extrude_curve", "revolve_curve" },
                ["Scripting"] = new List<string> { "execute_rhinoscript_python_code" },
                ["Debug"] = new List<string> { "set_debug_mode", "log_thought" }
            };

            foreach (var category in categories)
            {
                var availableInCategory = category.Value.Where(t => tools.Contains(t)).ToList();
                if (availableInCategory.Count > 0)
                {
                    RhinoApp.WriteLine($"  [{category.Key}]: {string.Join(", ", availableInCategory)}");
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
                // Scripting
                "execute_rhinoscript_python_code"
            };
        }

        public void Stop()
        {
            lock (lockObject)
            {
                running = false;
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

            RhinoApp.WriteLine("RhinoMCP server stopped");
        }

        private void ServerLoop()
        {
            RhinoApp.WriteLine("Server thread started");

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
                        RhinoApp.WriteLine($"Connected to client: {client.Client.RemoteEndPoint}");

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
                    RhinoApp.WriteLine($"Error in server loop: {e.Message}");

                    if (!IsRunning())
                        break;

                    Thread.Sleep(500);
                }
            }

            RhinoApp.WriteLine("Server thread stopped");
        }

        private void HandleClient(TcpClient client)
        {
            RhinoApp.WriteLine("Client handler started");

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
                                RhinoApp.WriteLine("Client disconnected");
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
                                                RhinoApp.WriteLine($"Failed to send response - client disconnected: {sendEx.Message}");
                                            }
                                        }
                                        catch (Exception e)
                                        {
                                            caughtException = e;
                                            RhinoApp.WriteLine($"Error executing command: {e.Message}\nStackTrace: {e.StackTrace}");
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
                                        RhinoApp.WriteLine("WARNING: Command execution timed out after 60 seconds");
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
                        RhinoApp.WriteLine($"Error receiving data: {e.Message}");
                        break;
                    }
                }
            }
            catch (Exception e)
            {
                RhinoApp.WriteLine($"Error in client handler: {e.Message}");
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
                RhinoApp.WriteLine("Client handler stopped");
            }
        }

        private JObject ExecuteCommand(JObject command)
        {
            string cmdType = command["type"]?.ToString();
            JObject parameters = command["params"] as JObject ?? new JObject();

            try
            {
                if (debugMode)
                {
                    RhinoApp.WriteLine($"Executing command: {cmdType} with parameters: {parameters.ToString()}");
                }

                JObject result = ExecuteCommandInternal(cmdType, parameters);

                if (debugMode)
                {
                    RhinoApp.WriteLine($"Command {cmdType} executed successfully");
                }
                return result;
            }
            catch (Exception e)
            {
                if (debugMode)
                {
                    RhinoApp.WriteLine($"Error executing command {cmdType}: {e.Message}\nStackTrace: {e.StackTrace}");
                }
                else
                {
                    RhinoApp.WriteLine($"Error executing command: {e.Message}");
                }
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
                // Add more handlers as needed
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
                    if (debugMode)
                    {
                        RhinoApp.WriteLine($"Error in handler for {cmdType}: {e.Message}\nStackTrace: {e.StackTrace}");
                    }
                    else
                    {
                        RhinoApp.WriteLine($"Error in handler: {e.Message}");
                    }
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