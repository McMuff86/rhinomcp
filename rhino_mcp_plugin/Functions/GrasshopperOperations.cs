using System;
using System.Collections.Generic;
using System.IO;
using System.Threading;
using System.Timers;
using Newtonsoft.Json.Linq;
using Rhino;

namespace RhinoMCPPlugin.Functions;

public partial class RhinoMCPFunctions
{
    /// <summary>
    /// Run a Grasshopper definition file using Rhino's Grasshopper Player.
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
    /// Run a Grasshopper definition file with automated parameter input.
    /// Uses sequenced RunScript calls with timing to automatically send parameter values.
    /// </summary>
    public JObject RunGrasshopperWithParams(JObject parameters)
    {
        string filePath = parameters["file_path"]?.ToString();
        if (string.IsNullOrEmpty(filePath))
            throw new ArgumentException("file_path is required");

        if (!File.Exists(filePath))
            throw new FileNotFoundException($"Grasshopper file not found: {filePath}");

        if (!filePath.ToLower().EndsWith(".gh"))
            throw new ArgumentException("file_path must be a .gh file");

        // Extract parameters with defaults
        int height = parameters["height"]?.Value<int>() ?? 2200;
        int width = parameters["width"]?.Value<int>() ?? 910;
        string plane = parameters["plane"]?.ToString() ?? "WorldXY";
        
        // Timing parameters (configurable for different scripts)
        int initialDelayMs = parameters["initial_delay_ms"]?.Value<int>() ?? 1500;
        int inputDelayMs = parameters["input_delay_ms"]?.Value<int>() ?? 300;

        RhinoApp.WriteLine("=== GRASSHOPPER AUTOMATION ===");
        RhinoApp.WriteLine($"Script: {filePath}");
        RhinoApp.WriteLine($"Parameters: height={height}, width={width}, plane={plane}");
        RhinoApp.WriteLine($"Timing: initial={initialDelayMs}ms, between inputs={inputDelayMs}ms");
        
        // Store inputs for sequenced execution
        var inputs = new List<string> { height.ToString(), width.ToString() };
        
        // Convert plane to Rhino format
        string planeInput = plane.ToLower() switch
        {
            "worldxy" => "0",       // Usually Enter/default for WorldXY
            "worldyz" => "1,0,0",   // Point defining YZ plane
            "worldzx" => "0,1,0",   // Point defining ZX plane
            _ => "0"                // Default
        };
        inputs.Add(planeInput);

        // 1. Start the Grasshopper script
        string script = $"_-GrasshopperPlayer \"{filePath}\"";
        RhinoApp.WriteLine($"Starting script: {script}");
        bool startResult = RhinoApp.RunScript(script, false);

        if (!startResult)
        {
            RhinoApp.WriteLine("ERROR: Failed to start Grasshopper script");
            throw new InvalidOperationException($"Failed to start Grasshopper definition: {filePath}");
        }

        // 2. Schedule automated inputs using a background thread
        var completionEvent = new ManualResetEventSlim(false);
        int inputIndex = 0;
        
        var inputTimer = new System.Timers.Timer(initialDelayMs);
        inputTimer.AutoReset = false;
        inputTimer.Elapsed += (sender, e) =>
        {
            // Schedule subsequent inputs
            ScheduleInputs(inputs, inputIndex, inputDelayMs, completionEvent);
        };
        inputTimer.Start();

        // Wait for completion with timeout (max 10 seconds)
        bool completed = completionEvent.Wait(TimeSpan.FromSeconds(10));
        inputTimer.Dispose();
        
        if (completed)
        {
            RhinoApp.WriteLine("=== AUTOMATION COMPLETE ===");
            return JObject.FromObject(new
            {
                file_path = filePath,
                status = "automated_complete",
                automated = true,
                parameters_used = new
                {
                    height = height,
                    width = width,
                    plane = plane
                },
                timing = new
                {
                    initial_delay_ms = initialDelayMs,
                    input_delay_ms = inputDelayMs
                }
            });
        }
        else
        {
            RhinoApp.WriteLine("=== AUTOMATION TIMEOUT - Manual input may be required ===");
            return JObject.FromObject(new
            {
                file_path = filePath,
                status = "automation_timeout",
                automated = false,
                parameters_expected = new
                {
                    height = height,
                    width = width,
                    plane = plane
                },
                note = "Automation timed out. You may need to enter remaining parameters manually."
            });
        }
    }

    /// <summary>
    /// Schedule automated inputs with delays between them.
    /// </summary>
    private void ScheduleInputs(List<string> inputs, int startIndex, int delayMs, ManualResetEventSlim completionEvent)
    {
        void SendNextInput(int index)
        {
            if (index >= inputs.Count)
            {
                // All inputs sent, signal completion
                completionEvent.Set();
                return;
            }

            // Send input on UI thread
            RhinoApp.InvokeOnUiThread(new Action(() =>
            {
                string input = inputs[index];
                RhinoApp.WriteLine($"Sending automated input [{index + 1}/{inputs.Count}]: {input}");
                RhinoApp.RunScript(input, false);
            }));

            // Schedule next input
            if (index + 1 < inputs.Count)
            {
                var nextTimer = new System.Timers.Timer(delayMs);
                nextTimer.AutoReset = false;
                nextTimer.Elapsed += (s, e) =>
                {
                    nextTimer.Dispose();
                    SendNextInput(index + 1);
                };
                nextTimer.Start();
            }
            else
            {
                // Last input sent, wait a bit then signal completion
                var finalTimer = new System.Timers.Timer(delayMs);
                finalTimer.AutoReset = false;
                finalTimer.Elapsed += (s, e) =>
                {
                    finalTimer.Dispose();
                    completionEvent.Set();
                };
                finalTimer.Start();
            }
        }

        SendNextInput(startIndex);
    }

    /// <summary>
    /// Run a Grasshopper definition with fully customizable parameter sequence.
    /// Uses background thread to avoid UI deadlock.
    /// </summary>
    public JObject RunGrasshopperAutomated(JObject parameters)
    {
        string filePath = parameters["file_path"]?.ToString();
        if (string.IsNullOrEmpty(filePath))
            throw new ArgumentException("file_path is required");

        if (!File.Exists(filePath))
            throw new FileNotFoundException($"Grasshopper file not found: {filePath}");

        if (!filePath.ToLower().EndsWith(".gh"))
            throw new ArgumentException("file_path must be a .gh file");

        // Get input sequence as JSON array
        var inputsArray = parameters["inputs"] as JArray;
        if (inputsArray == null || inputsArray.Count == 0)
            throw new ArgumentException("inputs array is required with at least one value");

        var inputs = new List<string>();
        foreach (var input in inputsArray)
        {
            inputs.Add(input.ToString());
        }

        // Timing parameters
        int initialDelayMs = parameters["initial_delay_ms"]?.Value<int>() ?? 1500;
        int inputDelayMs = parameters["input_delay_ms"]?.Value<int>() ?? 300;

        RhinoApp.WriteLine("=== GRASSHOPPER AUTOMATED EXECUTION ===");
        RhinoApp.WriteLine($"Script: {filePath}");
        RhinoApp.WriteLine($"Inputs: [{string.Join(", ", inputs)}]");
        RhinoApp.WriteLine($"Timing: initial={initialDelayMs}ms, between={inputDelayMs}ms");

        // 1. Start the Grasshopper script
        string script = $"_-GrasshopperPlayer \"{filePath}\"";
        RhinoApp.WriteLine($"Starting script...");
        bool startResult = RhinoApp.RunScript(script, false);

        if (!startResult)
        {
            throw new InvalidOperationException($"Failed to start Grasshopper definition: {filePath}");
        }

        // 2. Schedule automated inputs on a background thread
        // This avoids blocking the UI thread and prevents deadlock
        var inputsCopy = new List<string>(inputs);
        System.Threading.Tasks.Task.Run(() =>
        {
            try
            {
                // Wait for initial delay (script loading)
                Thread.Sleep(initialDelayMs);
                
                for (int i = 0; i < inputsCopy.Count; i++)
                {
                    string input = inputsCopy[i];
                    
                    // Send input on UI thread
                    RhinoApp.InvokeOnUiThread(new Action(() =>
                    {
                        RhinoApp.WriteLine($"Sending input [{i + 1}/{inputsCopy.Count}]: {input}");
                        RhinoApp.RunScript(input, false);
                    }));
                    
                    // Wait between inputs
                    if (i < inputsCopy.Count - 1)
                    {
                        Thread.Sleep(inputDelayMs);
                    }
                }
                
                RhinoApp.InvokeOnUiThread(new Action(() =>
                {
                    RhinoApp.WriteLine("=== ALL INPUTS SENT ===");
                }));
            }
            catch (Exception ex)
            {
                RhinoApp.InvokeOnUiThread(new Action(() =>
                {
                    RhinoApp.WriteLine($"ERROR in automation: {ex.Message}");
                }));
            }
        });

        // 3. Return immediately - inputs will be sent in background
        RhinoApp.WriteLine("Automation scheduled - inputs will be sent shortly...");

        return JObject.FromObject(new
        {
            file_path = filePath,
            status = "automation_started",
            automated = true,
            inputs_scheduled = inputs,
            timing = new
            {
                initial_delay_ms = initialDelayMs,
                input_delay_ms = inputDelayMs
            },
            note = "Inputs will be sent automatically after initial delay"
        });
    }

    /// <summary>
    /// Create door geometry from building plan analysis.
    /// </summary>
    public JObject CreateDoorFromPlan(JObject parameters)
    {
        // This would analyze plan text and create appropriate doors
        // For now, delegate to the automated Grasshopper tool
        return RunGrasshopperWithParams(parameters);
    }

    /// <summary>
    /// Generate bill of materials from created geometry.
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
}