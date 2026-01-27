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

        public static void StartServer(string host = "127.0.0.1")
        {
            // Check if plugin already started a server during auto-start
            var pluginServer = RhinoMCPPlugin.Instance?.Server;
            if (pluginServer != null)
            {
                // Plugin server exists - stop it if running with different host
                if (pluginServer.IsRunning())
                {
                    pluginServer.Stop();
                }
            }

            // Stop existing controller server if any
            if (server != null && server.IsRunning())
            {
                server.Stop();
            }

            // Create new server with specified host
            server = new RhinoMCPServer(host);
            server.Start();
        }

        public static void StopServer()
        {
            // Check if we're using the plugin's server
            var pluginServer = RhinoMCPPlugin.Instance?.Server;
            if (pluginServer != null)
            {
                pluginServer.Stop();
                return;
            }

            // Stop our own server
            if (server != null)
            {
                server.Stop();
                server = null;
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
