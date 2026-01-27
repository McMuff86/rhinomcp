using System;
using Rhino;
using Rhino.Commands;
using Rhino.Input;
using Rhino.Input.Custom;

namespace RhinoMCPPlugin.Commands
{
    /// <summary>
    /// Command to set the RhinoMCP log level.
    /// Usage: mcploglevel [error|warning|info|debug|verbose]
    /// </summary>
    public class MCPLogLevelCommand : Command
    {
        public MCPLogLevelCommand()
        {
            Instance = this;
        }

        public static MCPLogLevelCommand Instance { get; private set; }

        public override string EnglishName => "mcploglevel";

        protected override Result RunCommand(RhinoDoc doc, RunMode mode)
        {
            // Show current level if no argument
            var currentLevel = Logger.CurrentLevel;
            
            // Get level from command line
            var go = new GetOption();
            go.SetCommandPrompt($"Set log level (current: {currentLevel})");
            
            var errorIdx = go.AddOption("Error");
            var warnIdx = go.AddOption("Warning");
            var infoIdx = go.AddOption("Info");
            var debugIdx = go.AddOption("Debug");
            var verboseIdx = go.AddOption("Verbose");
            
            var result = go.Get();
            
            if (result == GetResult.Option)
            {
                var selectedIdx = go.OptionIndex();
                LogLevel newLevel;
                
                if (selectedIdx == errorIdx) newLevel = LogLevel.Error;
                else if (selectedIdx == warnIdx) newLevel = LogLevel.Warning;
                else if (selectedIdx == infoIdx) newLevel = LogLevel.Info;
                else if (selectedIdx == debugIdx) newLevel = LogLevel.Debug;
                else if (selectedIdx == verboseIdx) newLevel = LogLevel.Verbose;
                else return Result.Cancel;
                
                Logger.CurrentLevel = newLevel;
                Logger.Raw($"Log level set to: {newLevel}");
                Logger.Raw(GetLevelDescription(newLevel));
            }
            else if (result == GetResult.Nothing)
            {
                // Just show current level
                Logger.Raw($"Current log level: {currentLevel}");
                Logger.Raw(GetLevelDescription(currentLevel));
            }
            else
            {
                return Result.Cancel;
            }
            
            return Result.Success;
        }
        
        private string GetLevelDescription(LogLevel level)
        {
            return level switch
            {
                LogLevel.Error => "  Shows: Errors only",
                LogLevel.Warning => "  Shows: Errors, Warnings",
                LogLevel.Info => "  Shows: Errors, Warnings, Status updates",
                LogLevel.Debug => "  Shows: Errors, Warnings, Status, Operation details",
                LogLevel.Verbose => "  Shows: Everything (verbose tracing)",
                _ => ""
            };
        }
    }
}
