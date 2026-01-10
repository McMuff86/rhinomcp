using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Rhino;

namespace RhinoMCPPlugin
{
    class RhinoMCPServerController
    {
        private static RhinoMCPServer server;

        public static void StartServer()
        {
            // Check if plugin already started a server during auto-start
            var pluginServer = RhinoMCPPlugin.Instance?.Server;
            if (pluginServer != null)
            {
                // Plugin server exists, just ensure it's started
                if (!pluginServer.IsRunning())
                {
                    pluginServer.Start();
                }
                RhinoApp.WriteLine("Server started (using existing plugin server).");
                return;
            }

            // No plugin server, create our own
            if (server == null)
            {
                server = new RhinoMCPServer();
            }

            server.Start();
            RhinoApp.WriteLine("Server started.");
        }

        public static void StopServer()
        {
            // Check if we're using the plugin's server
            var pluginServer = RhinoMCPPlugin.Instance?.Server;
            if (pluginServer != null)
            {
                pluginServer.Stop();
                RhinoApp.WriteLine("Server stopped (plugin server).");
                return;
            }

            // Stop our own server
            if (server != null)
            {
                server.Stop();
                server = null;
                RhinoApp.WriteLine("Server stopped.");
            }
        }

        public static bool IsServerRunning()
        {
            // Check both plugin server and controller server
            var pluginServer = RhinoMCPPlugin.Instance?.Server;
            if (pluginServer != null && pluginServer.IsRunning())
            {
                return true;
            }

            return server != null && server.IsRunning();
        }
    }
}
