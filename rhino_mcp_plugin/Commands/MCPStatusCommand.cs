using System;
using Rhino;
using Rhino.Commands;

namespace RhinoMCPPlugin.Commands
{
    public class MCPStatusCommand : Command
    {
        public MCPStatusCommand()
        {
            Instance = this;
        }

        public static MCPStatusCommand Instance { get; private set; }

        public override string EnglishName => "MCPStatus";

        protected override Result RunCommand(RhinoDoc doc, RunMode mode)
        {
            var plugin = RhinoMCPPlugin.Instance;
            if (plugin?.Server == null)
            {
                RhinoApp.WriteLine("MCP Server is not running.");
                return Result.Success;
            }

            bool debugMode = plugin.Server.GetDebugMode();
            var wsStatus = plugin.Server.GetWebSocketStatus();
            string host = plugin.Server.GetHost();
            int port = plugin.Server.GetPort();
            bool isRemote = plugin.Server.IsRemoteAccessEnabled();
            
            string serverMode = isRemote ? "TCP (remote access)" : "MCP (localhost only)";
            
            RhinoApp.WriteLine($"RhinoMCP Server Status:");
            RhinoApp.WriteLine($"  - Mode: {serverMode}");
            RhinoApp.WriteLine($"  - TCP Server: Active on {host}:{port}");
            RhinoApp.WriteLine($"  - Debug Mode: {(debugMode ? "Enabled" : "Disabled")}");
            
            if (wsStatus.IsRunning)
            {
                RhinoApp.WriteLine($"  - WebSocket: Active on {wsStatus.Endpoint} ({wsStatus.ClientCount} clients)");
            }
            else
            {
                RhinoApp.WriteLine($"  - WebSocket: Not running");
            }

            return Result.Success;
        }
    }
}
