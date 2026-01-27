using System;
using System.Collections.Generic;
using Rhino;
using Rhino.Commands;
using Rhino.Geometry;
using Rhino.Input;
using Rhino.Input.Custom;
using System.ComponentModel;
using System.Threading.Tasks;

namespace RhinoMCPPlugin.Commands
{
    /// <summary>
    /// Starts the RhinoMCP server bound to 127.0.0.1 (localhost only).
    /// Use this command for local MCP clients like Cursor or Claude Desktop.
    /// For remote/WSL access, use 'tcpstart' instead.
    /// </summary>
    public class MCPStartCommand : Command
    {
        public MCPStartCommand()
        {
            // Rhino only creates one instance of each command class defined in a
            // plug-in, so it is safe to store a refence in a static property.
            Instance = this;
        }

        ///<summary>The only instance of this command.</summary>
        public static MCPStartCommand Instance { get; private set; }

        

        public override string EnglishName => "mcpstart";

        protected override Result RunCommand(RhinoDoc doc, RunMode mode)
        {
            // Start server on 127.0.0.1 for local access (Cursor, Claude Desktop)
            RhinoMCPServerController.StartServer("127.0.0.1");
            return Result.Success;
        }

    }
}
