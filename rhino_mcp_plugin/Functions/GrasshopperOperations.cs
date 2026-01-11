using System;
using System.Collections.Generic;
using System.IO;
using System.Threading;
using Newtonsoft.Json.Linq;
using Rhino;

namespace RhinoMCPPlugin.Functions;

/// <summary>
/// Grasshopper-related operations for the RhinoMCP plugin.
/// 
/// For interactive Grasshopper scripts that require user input,
/// use the WebSocket-based approach:
/// 1. Start script with StartScriptAsync (via TCP or WebSocket)
/// 2. Monitor prompts via WebSocket events
/// 3. Send inputs with SendCommandInput
/// </summary>
public partial class RhinoMCPFunctions
{
    /// <summary>
    /// Run a Grasshopper definition file using Rhino's Grasshopper Player.
    /// Note: This blocks until all prompts are answered manually.
    /// For automated input, use StartScriptAsync + WebSocket monitoring.
    /// </summary>
    public JObject RunGrasshopper(JObject parameters)
    {
        string filePath = parameters["file_path"]?.ToString();
        if (string.IsNullOrEmpty(filePath))
            throw new ArgumentException("file_path is required");

        if (!File.Exists(filePath))
            throw new FileNotFoundException($"Grasshopper file not found: {filePath}");

        if (!filePath.ToLower().EndsWith(".gh"))
            throw new ArgumentException("file_path must be a .gh file");

        // Use Rhino's GrasshopperPlayer command to run the definition
        string script = $"_-GrasshopperPlayer \"{filePath}\"";
        bool result = RhinoApp.RunScript(script, false);

        if (!result)
            throw new InvalidOperationException($"Failed to run Grasshopper definition: {filePath}");

        return JObject.FromObject(new
        {
            file_path = filePath,
            status = "executed"
        });
    }

    /// <summary>
    /// Generate bill of materials from created geometry.
    /// Placeholder implementation - to be expanded based on requirements.
    /// </summary>
    public JObject GenerateBillOfMaterials(JObject parameters)
    {
        // This would analyze created objects and generate BOM
        // For now, return a placeholder response
        return JObject.FromObject(new
        {
            materials = new Dictionary<string, int>
            {
                { "Door Frame", 1 },
                { "Wall Panel", 4 },
                { "Window Frame", 2 }
            },
            total_items = 7,
            status = "bom_generated"
        });
    }

    /// <summary>
    /// Start a Rhino script asynchronously (non-blocking).
    /// Returns immediately, allowing the caller to monitor WebSocket for prompts.
    /// 
    /// Use this for interactive scripts like GrasshopperPlayer:
    /// 1. Call StartScriptAsync to start the script
    /// 2. Monitor WebSocket for Prompt events
    /// 3. Send inputs via WebSocket send_input command or SendCommandInput
    /// </summary>
    public JObject StartScriptAsync(JObject parameters)
    {
        string script = parameters["script"]?.ToString();
        if (string.IsNullOrEmpty(script))
            throw new ArgumentException("script is required");

        RhinoApp.WriteLine($"[ASYNC] Starting script: {script}");

        // Run the script on UI thread but don't wait for it
        System.Threading.Tasks.Task.Run(() =>
        {
            Thread.Sleep(50); // Small delay to let TCP response go first
            RhinoApp.InvokeOnUiThread(new Action(() =>
            {
                try
                {
                    RhinoApp.WriteLine($"[ASYNC] Executing: {script}");
                    bool result = RhinoApp.RunScript(script, false);
                    RhinoApp.WriteLine($"[ASYNC] Script completed: {result}");
                }
                catch (Exception ex)
                {
                    RhinoApp.WriteLine($"[ASYNC] Script error: {ex.Message}");
                }
            }));
        });

        return JObject.FromObject(new
        {
            status = "started",
            script = script,
            note = "Script started asynchronously. Monitor WebSocket for prompts."
        });
    }

    /// <summary>
    /// Send input to the Rhino command line.
    /// Use this to respond to prompts detected via WebSocket.
    /// 
    /// Note: Prefer using WebSocket send_input command for faster response.
    /// This TCP-based method is kept for backwards compatibility.
    /// </summary>
    public JObject SendCommandInput(JObject parameters)
    {
        string input = parameters["input"]?.ToString();
        if (input == null)
            throw new ArgumentException("input is required");

        RhinoApp.WriteLine($"[INPUT] Sending: {input}");

        // Send the input directly to the command line
        bool result = RhinoApp.RunScript(input, false);

        return JObject.FromObject(new
        {
            status = result ? "sent" : "failed",
            input = input
        });
    }

    /// <summary>
    /// Get the current Rhino command prompt text.
    /// Useful for debugging and checking Rhino's state.
    /// 
    /// Note: Prefer using WebSocket get_state command for real-time updates.
    /// </summary>
    public JObject GetCurrentPrompt(JObject parameters)
    {
        string prompt = RhinoApp.CommandPrompt ?? "";
        
        return JObject.FromObject(new
        {
            prompt = prompt,
            timestamp = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss.fff")
        });
    }
}
