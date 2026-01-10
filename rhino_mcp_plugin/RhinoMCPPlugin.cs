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
        /// Called when the plug-in is being loaded. Start the MCP server automatically.
        /// </summary>
        protected override Rhino.PlugIns.LoadReturnCode OnLoad(ref string errorMessage)
        {
            try
            {
                // Start MCP server automatically when plugin loads
                if (Server == null)
                {
                    Server = new RhinoMCPServer();
                }

                // Start server in background thread
                System.Threading.Tasks.Task.Run(() =>
                {
                    try
                    {
                        Server.Start();
                        RhinoApp.WriteLine("RhinoMCP Plugin loaded and server started automatically.");
                    }
                    catch (Exception ex)
                    {
                        RhinoApp.WriteLine($"Failed to start MCP server: {ex.Message}");
                    }
                });

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
                    RhinoApp.WriteLine("RhinoMCP Plugin unloaded and server stopped.");
                }
            }
            catch (Exception ex)
            {
                RhinoApp.WriteLine($"Error stopping MCP server: {ex.Message}");
            }

            base.OnShutdown();
        }

        // You can override methods here to change the plug-in behavior on
        // loading and shut down, add options pages to the Rhino _Option command
        // and maintain plug-in wide options in a document.
    }
}