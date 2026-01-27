using System;
using Rhino;

namespace RhinoMCPPlugin
{
    ///<summary>
    /// <para>Every RhinoCommon .rhp assembly must have one and only one PlugIn-derived
    /// class. DO NOT create instances of this class yourself. It is the
    /// responsibility of Rhino to create an instance of this class.</para>
    /// <para>To complete plug-in information, please also see all PlugInDescription
    /// attributes in AssemblyInfo.cs (you might need to click "Project" ->
    /// "Show All Files" to see it in the "Solution Explorer" window).</para>
    ///</summary>
    public class RhinoMCPPlugin : Rhino.PlugIns.PlugIn
    {
        public RhinoMCPPlugin()
        {
            Instance = this;
        }
        
        ///<summary>Gets the only instance of the RhinoMCPPlugin plug-in.</summary>
        public static RhinoMCPPlugin Instance { get; private set; }

        public RhinoMCPServer Server { get; set; }

        /// <summary>
        /// Called when the plug-in is being loaded.
        /// Server is NOT started automatically - use mcpstart or tcpstart command.
        /// </summary>
        protected override Rhino.PlugIns.LoadReturnCode OnLoad(ref string errorMessage)
        {
            try
            {
                Logger.Info("RhinoMCP Plugin loaded. Use 'mcpstart' or 'tcpstart' to start the server.");
                return Rhino.PlugIns.LoadReturnCode.Success;
            }
            catch (Exception ex)
            {
                errorMessage = ex.Message;
                return Rhino.PlugIns.LoadReturnCode.ErrorShowDialog;
            }
        }

        /// <summary>
        /// Called when the plug-in is being unloaded. Stop the MCP server.
        /// </summary>
        protected override void OnShutdown()
        {
            try
            {
                if (Server != null)
                {
                    Server.Stop();
                    Logger.Info("RhinoMCP Plugin unloaded");
                }
            }
            catch (Exception ex)
            {
                Logger.Error("Error stopping MCP server", ex);
            }

            base.OnShutdown();
        }

        // You can override methods here to change the plug-in behavior on
        // loading and shut down, add options pages to the Rhino _Option command
        // and maintain plug-in wide options in a document.
    }
}