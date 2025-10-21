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
            RhinoApp.WriteLine($"MCP Server Status:");
            RhinoApp.WriteLine($"  - Debug Mode: {(debugMode ? "Enabled" : "Disabled")}");
            RhinoApp.WriteLine($"  - Connection: Active on 127.0.0.1:1999");
            RhinoApp.WriteLine($"  - Active Features: {(debugMode ? "Enhanced Logging, AI Thoughts" : "Basic Logging")}");

            return Result.Success;
        }
    }
}
