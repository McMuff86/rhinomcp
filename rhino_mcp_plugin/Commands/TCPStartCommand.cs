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
    /// Starts the RhinoMCP server bound to 0.0.0.0 for remote/WSL access.
    /// Use this command when connecting from WSL, Clawdbot, or other network clients.
    /// </summary>
    public class TCPStartCommand : Command
    {
        public TCPStartCommand()
        {
            Instance = this;
        }

        public static TCPStartCommand Instance { get; private set; }

        public override string EnglishName => "tcpstart";

        protected override Result RunCommand(RhinoDoc doc, RunMode mode)
        {
            // Start server on 0.0.0.0 for remote access
            RhinoMCPServerController.StartServer("0.0.0.0");
            return Result.Success;
        }
    }
}
