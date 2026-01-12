using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using Fleck;
using Newtonsoft.Json.Linq;
using Rhino;

namespace RhinoMCPPlugin
{
    /// <summary>
    /// WebSocket server for real-time command line event streaming.
    /// Provides push-based notifications to AI agents about Rhino's state.
    /// </summary>
    public class RhinoMCPWebSocketServer
    {
        private WebSocketServer server;
        private Thread monitorThread;
        private bool isRunning = false;
        private readonly List<IWebSocketConnection> clients = new List<IWebSocketConnection>();
        private readonly object clientsLock = new object();

        private string lastCommandPrompt = "";
        private string lastCommandHistory = "";
        private const int MonitorIntervalMs = 100; // Check every 100ms
        private const int HeartbeatIntervalMs = 30000; // Ping every 30 seconds
        private DateTime lastHeartbeat = DateTime.Now;

        private string host;
        private int port;

        /// <summary>
        /// Gets whether the WebSocket server is currently running.
        /// </summary>
        public bool IsRunning => isRunning;

        /// <summary>
        /// Gets the number of connected clients.
        /// </summary>
        public int ClientCount
        {
            get
            {
                lock (clientsLock)
                {
                    return clients.Count;
                }
            }
        }

        /// <summary>
        /// Gets the WebSocket endpoint URL.
        /// </summary>
        public string Endpoint => $"ws://{host}:{port}";

        /// <summary>
        /// Start the WebSocket server.
        /// </summary>
        /// <param name="host">Host address (default: 127.0.0.1)</param>
        /// <param name="port">Port number (default: 2000)</param>
        public void Start(string host = "127.0.0.1", int port = 2000)
        {
            if (isRunning)
            {
                RhinoApp.WriteLine("WebSocket server already running");
                return;
            }

            this.host = host;
            this.port = port;

            try
            {
                // Configure Fleck logging
                FleckLog.Level = LogLevel.Error;

                // Start WebSocket server
                server = new WebSocketServer($"ws://{host}:{port}");

                server.Start(socket =>
                {
                    socket.OnOpen = () => OnClientConnected(socket);
                    socket.OnClose = () => OnClientDisconnected(socket);
                    socket.OnMessage = message => HandleClientMessage(socket, message);
                    socket.OnError = ex => OnClientError(socket, ex);
                });

                // Start monitoring thread
                isRunning = true;
                lastCommandPrompt = RhinoApp.CommandPrompt ?? "";
                lastCommandHistory = RhinoApp.CommandHistoryWindowText ?? "";

                monitorThread = new Thread(MonitorCommandLine);
                monitorThread.IsBackground = true;
                monitorThread.Start();

                RhinoApp.WriteLine($"WebSocket server started on ws://{host}:{port}");
            }
            catch (Exception e)
            {
                RhinoApp.WriteLine($"Failed to start WebSocket server: {e.Message}");
                Stop();
            }
        }

        /// <summary>
        /// Stop the WebSocket server.
        /// </summary>
        public void Stop()
        {
            isRunning = false;

            // Stop monitoring thread
            if (monitorThread != null)
            {
                try
                {
                    monitorThread.Join(1000);
                }
                catch
                {
                    // Ignore errors on join
                }
                monitorThread = null;
            }

            // Close all client connections
            lock (clientsLock)
            {
                foreach (var client in clients.ToList())
                {
                    try
                    {
                        client.Close();
                    }
                    catch
                    {
                        // Ignore errors on close
                    }
                }
                clients.Clear();
            }

            // Dispose server
            if (server != null)
            {
                try
                {
                    server.Dispose();
                }
                catch
                {
                    // Ignore errors on dispose
                }
                server = null;
            }

            RhinoApp.WriteLine("WebSocket server stopped");
        }

        /// <summary>
        /// Handle new client connection.
        /// </summary>
        private void OnClientConnected(IWebSocketConnection socket)
        {
            lock (clientsLock)
            {
                clients.Add(socket);
            }

            RhinoApp.WriteLine($"WebSocket client connected: {socket.ConnectionInfo.ClientIpAddress}:{socket.ConnectionInfo.ClientPort}");

            // Send welcome message with current state
            try
            {
                var welcomeMessage = new JObject
                {
                    ["type"] = "Connected",
                    ["timestamp"] = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss.fff"),
                    ["current_prompt"] = RhinoApp.CommandPrompt ?? ""
                };
                socket.Send(welcomeMessage.ToString());
            }
            catch (Exception ex)
            {
                RhinoApp.WriteLine($"Error sending welcome message: {ex.Message}");
            }
        }

        /// <summary>
        /// Handle client disconnection.
        /// </summary>
        private void OnClientDisconnected(IWebSocketConnection socket)
        {
            lock (clientsLock)
            {
                clients.Remove(socket);
            }

            RhinoApp.WriteLine($"WebSocket client disconnected");
        }

        /// <summary>
        /// Handle client error.
        /// </summary>
        private void OnClientError(IWebSocketConnection socket, Exception ex)
        {
            RhinoApp.WriteLine($"WebSocket client error: {ex.Message}");

            lock (clientsLock)
            {
                clients.Remove(socket);
            }
        }

        /// <summary>
        /// Handle incoming client messages.
        /// </summary>
        private void HandleClientMessage(IWebSocketConnection socket, string message)
        {
            try
            {
                var msg = JObject.Parse(message);
                string command = msg["command"]?.ToString()?.ToLower();

                switch (command)
                {
                    case "ping":
                        // Health check
                        socket.Send(new JObject
                        {
                            ["type"] = "Pong",
                            ["timestamp"] = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss.fff")
                        }.ToString());
                        break;

                    case "get_state":
                        // Return current command line state
                        socket.Send(new JObject
                        {
                            ["type"] = "State",
                            ["timestamp"] = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss.fff"),
                            ["current_prompt"] = RhinoApp.CommandPrompt ?? ""
                        }.ToString());
                        break;

                    case "send_input":
                        // Send input to Rhino command line (via WebSocket)
                        HandleSendInput(socket, msg);
                        break;

                    case "run_script":
                        // Run a script asynchronously
                        HandleRunScript(socket, msg);
                        break;

                    case "cancel":
                        // Cancel current command
                        HandleCancel(socket);
                        break;

                    default:
                        socket.Send(new JObject
                        {
                            ["type"] = "Error",
                            ["message"] = $"Unknown command: {command}"
                        }.ToString());
                        break;
                }
            }
            catch (Exception ex)
            {
                RhinoApp.WriteLine($"Error handling WebSocket message: {ex.Message}");
                try
                {
                    socket.Send(new JObject
                    {
                        ["type"] = "Error",
                        ["message"] = ex.Message
                    }.ToString());
                }
                catch
                {
                    // Ignore send errors
                }
            }
        }

        /// <summary>
        /// Handle send_input command - sends input to Rhino command line.
        /// </summary>
        private void HandleSendInput(IWebSocketConnection socket, JObject msg)
        {
            string input = msg["input"]?.ToString() ?? "";
            string requestId = msg["request_id"]?.ToString();

            RhinoApp.InvokeOnUiThread(new Action(() =>
            {
                try
                {
                    bool result = RhinoApp.RunScript(input, false);
                    var response = new JObject
                    {
                        ["type"] = "InputResult",
                        ["timestamp"] = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss.fff"),
                        ["success"] = result,
                        ["input"] = input
                    };
                    if (!string.IsNullOrEmpty(requestId))
                        response["request_id"] = requestId;

                    socket.Send(response.ToString());
                }
                catch (Exception ex)
                {
                    socket.Send(new JObject
                    {
                        ["type"] = "Error",
                        ["message"] = $"Failed to send input: {ex.Message}",
                        ["request_id"] = requestId
                    }.ToString());
                }
            }));
        }

        /// <summary>
        /// Handle run_script command - starts a script asynchronously.
        /// </summary>
        private void HandleRunScript(IWebSocketConnection socket, JObject msg)
        {
            string script = msg["script"]?.ToString();
            string requestId = msg["request_id"]?.ToString();

            if (string.IsNullOrEmpty(script))
            {
                socket.Send(new JObject
                {
                    ["type"] = "Error",
                    ["message"] = "Script is required",
                    ["request_id"] = requestId
                }.ToString());
                return;
            }

            // Acknowledge immediately
            socket.Send(new JObject
            {
                ["type"] = "ScriptStarted",
                ["timestamp"] = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss.fff"),
                ["script"] = script,
                ["request_id"] = requestId
            }.ToString());

            // Run script on UI thread (non-blocking from WebSocket perspective)
            System.Threading.Tasks.Task.Run(() =>
            {
                Thread.Sleep(50); // Small delay to let acknowledgment go first
                RhinoApp.InvokeOnUiThread(new Action(() =>
                {
                    try
                    {
                        bool result = RhinoApp.RunScript(script, false);
                        // Broadcast completion to all clients
                        BroadcastEvent(new JObject
                        {
                            ["type"] = "ScriptCompleted",
                            ["timestamp"] = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss.fff"),
                            ["script"] = script,
                            ["success"] = result,
                            ["request_id"] = requestId
                        });
                    }
                    catch (Exception ex)
                    {
                        BroadcastEvent(new JObject
                        {
                            ["type"] = "ScriptError",
                            ["timestamp"] = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss.fff"),
                            ["script"] = script,
                            ["error"] = ex.Message,
                            ["request_id"] = requestId
                        });
                    }
                }));
            });
        }

        /// <summary>
        /// Handle cancel command - attempts to cancel current operation.
        /// Sends Escape key to Rhino to cancel any hanging command.
        /// </summary>
        private void HandleCancel(IWebSocketConnection socket)
        {
            RhinoApp.InvokeOnUiThread(new Action(() =>
            {
                try
                {
                    // Send Escape key to cancel current command (like pressing Esc)
                    // This is more reliable than _Cancel for emergency situations
                    RhinoApp.RunScript("_Esc", false);
                    
                    // Also try _Cancel as fallback
                    RhinoApp.RunScript("_Cancel", false);
                    
                    socket.Send(new JObject
                    {
                        ["type"] = "CancelResult",
                        ["timestamp"] = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss.fff"),
                        ["success"] = true,
                        ["method"] = "Esc + Cancel"
                    }.ToString());
                }
                catch (Exception ex)
                {
                    socket.Send(new JObject
                    {
                        ["type"] = "Error",
                        ["message"] = $"Failed to cancel: {ex.Message}"
                    }.ToString());
                }
            }));
        }

        /// <summary>
        /// Background thread that monitors command line changes.
        /// </summary>
        private void MonitorCommandLine()
        {
            while (isRunning)
            {
                try
                {
                    // Check for command prompt changes
                    string currentPrompt = RhinoApp.CommandPrompt ?? "";
                    if (currentPrompt != lastCommandPrompt && !string.IsNullOrEmpty(currentPrompt))
                    {
                        BroadcastEvent(new JObject
                        {
                            ["type"] = "Prompt",
                            ["timestamp"] = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss.fff"),
                            ["text"] = currentPrompt
                        });
                        lastCommandPrompt = currentPrompt;
                    }

                    // Check for command history changes
                    string historyText = RhinoApp.CommandHistoryWindowText ?? "";
                    if (historyText != lastCommandHistory && !string.IsNullOrEmpty(historyText))
                    {
                        // Find what's new (history only appends)
                        if (historyText.StartsWith(lastCommandHistory))
                        {
                            string newText = historyText.Substring(lastCommandHistory.Length);
                            if (!string.IsNullOrWhiteSpace(newText))
                            {
                                var newLines = newText.Split(new[] { '\r', '\n' }, StringSplitOptions.RemoveEmptyEntries);
                                foreach (var line in newLines)
                                {
                                    if (!string.IsNullOrWhiteSpace(line))
                                    {
                                        BroadcastEvent(new JObject
                                        {
                                            ["type"] = "History",
                                            ["timestamp"] = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss.fff"),
                                            ["text"] = line
                                        });
                                    }
                                }
                            }
                        }
                        lastCommandHistory = historyText;
                    }

                    // Send heartbeat ping to all clients periodically
                    if ((DateTime.Now - lastHeartbeat).TotalMilliseconds >= HeartbeatIntervalMs)
                    {
                        BroadcastEvent(new JObject
                        {
                            ["type"] = "Heartbeat",
                            ["timestamp"] = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss.fff")
                        });
                        lastHeartbeat = DateTime.Now;
                    }
                }
                catch (Exception ex)
                {
                    // Log but don't crash the monitoring thread
                    RhinoApp.WriteLine($"Error in WebSocket monitor: {ex.Message}");
                }

                Thread.Sleep(MonitorIntervalMs);
            }
        }

        /// <summary>
        /// Broadcast an event to all connected clients.
        /// </summary>
        private void BroadcastEvent(JObject eventData)
        {
            string json = eventData.ToString(Newtonsoft.Json.Formatting.None);

            // Take a snapshot of clients to avoid holding lock during send
            List<IWebSocketConnection> clientSnapshot;
            lock (clientsLock)
            {
                clientSnapshot = clients.ToList();
            }

            // Send to all clients
            var failedClients = new List<IWebSocketConnection>();

            foreach (var client in clientSnapshot)
            {
                try
                {
                    client.Send(json);
                }
                catch (Exception)
                {
                    failedClients.Add(client);
                }
            }

            // Remove failed clients
            if (failedClients.Count > 0)
            {
                lock (clientsLock)
                {
                    foreach (var failed in failedClients)
                    {
                        clients.Remove(failed);
                    }
                }
            }
        }
    }
}
