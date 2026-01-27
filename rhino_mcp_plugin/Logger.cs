using System;
using System.IO;
using Rhino;

namespace RhinoMCPPlugin
{
    /// <summary>
    /// Log levels for RhinoMCP plugin output.
    /// </summary>
    public enum LogLevel
    {
        /// <summary>Only errors that prevent operations.</summary>
        Error = 0,
        /// <summary>Errors + warnings about potential issues.</summary>
        Warning = 1,
        /// <summary>Errors + warnings + important status updates (server start/stop, etc.).</summary>
        Info = 2,
        /// <summary>Detailed information for debugging (object IDs, operation details).</summary>
        Debug = 3,
        /// <summary>Everything, including verbose operation traces.</summary>
        Verbose = 4
    }

    /// <summary>
    /// Centralized logger for RhinoMCP plugin.
    /// </summary>
    public static class Logger
    {
        private static LogLevel _currentLevel = LogLevel.Verbose;
        private static readonly object _lock = new object();
        private static readonly object _fileLock = new object();
        private static string _logFilePath;
        private static bool _fileLoggingEnabled = true;
        private static StreamWriter _logWriter;

        /// <summary>
        /// Static constructor - initializes file logging.
        /// </summary>
        static Logger()
        {
            try
            {
                // Log to %TEMP%\rhinomcp.log
                _logFilePath = Path.Combine(Path.GetTempPath(), "rhinomcp.log");
                
                // Truncate file on startup (fresh log each session)
                _logWriter = new StreamWriter(_logFilePath, append: false) { AutoFlush = true };
                _fileLoggingEnabled = true;
            }
            catch
            {
                _fileLoggingEnabled = false;
            }
        }

        /// <summary>
        /// Gets the log file path.
        /// </summary>
        public static string LogFilePath => _logFilePath;

        /// <summary>
        /// Gets or sets whether file logging is enabled.
        /// </summary>
        public static bool FileLoggingEnabled
        {
            get { return _fileLoggingEnabled; }
            set { _fileLoggingEnabled = value; }
        }

        /// <summary>
        /// Gets or sets the current log level.
        /// </summary>
        public static LogLevel CurrentLevel
        {
            get { lock (_lock) { return _currentLevel; } }
            set { lock (_lock) { _currentLevel = value; } }
        }

        /// <summary>
        /// Sets log level from string (for commands).
        /// </summary>
        public static bool SetLevel(string levelName)
        {
            if (Enum.TryParse<LogLevel>(levelName, true, out var level))
            {
                CurrentLevel = level;
                return true;
            }
            return false;
        }

        /// <summary>
        /// Log an error message (always shown unless level is below Error).
        /// </summary>
        public static void Error(string message)
        {
            if (CurrentLevel >= LogLevel.Error)
                WriteLine("[ERROR]", message);
        }

        /// <summary>
        /// Log an error with exception details.
        /// </summary>
        public static void Error(string message, Exception ex)
        {
            if (CurrentLevel >= LogLevel.Error)
                WriteLine("[ERROR]", $"{message}: {ex.Message}");
        }

        /// <summary>
        /// Log a warning message.
        /// </summary>
        public static void Warning(string message)
        {
            if (CurrentLevel >= LogLevel.Warning)
                WriteLine("[WARN]", message);
        }

        /// <summary>
        /// Log an info message (important status updates).
        /// </summary>
        public static void Info(string message)
        {
            if (CurrentLevel >= LogLevel.Info)
                WriteLine("[INFO]", message);
        }

        /// <summary>
        /// Log a debug message (operation details).
        /// </summary>
        public static void Debug(string message)
        {
            if (CurrentLevel >= LogLevel.Debug)
                WriteLine("[DEBUG]", message);
        }

        /// <summary>
        /// Log a verbose message (everything).
        /// </summary>
        public static void Verbose(string message)
        {
            if (CurrentLevel >= LogLevel.Verbose)
                WriteLine("[TRACE]", message);
        }

        /// <summary>
        /// Log a message with custom category prefix.
        /// </summary>
        public static void Debug(string category, string message)
        {
            if (CurrentLevel >= LogLevel.Debug)
                WriteLine($"[{category}]", message);
        }

        /// <summary>
        /// Log a verbose message with custom category prefix.
        /// </summary>
        public static void Verbose(string category, string message)
        {
            if (CurrentLevel >= LogLevel.Verbose)
                WriteLine($"[{category}]", message);
        }

        /// <summary>
        /// Raw output without level check (for startup banners, etc.)
        /// </summary>
        public static void Raw(string message)
        {
            RhinoApp.WriteLine(message);
            
            var timestamp = DateTime.Now.ToString("HH:mm:ss.fff");
            WriteToFile($"[{timestamp}] {message}");
        }

        private static void WriteLine(string prefix, string message)
        {
            var timestamp = DateTime.Now.ToString("HH:mm:ss.fff");
            var fullMessage = $"{prefix} {message}";
            var fileMessage = $"[{timestamp}] {fullMessage}";
            
            // Write to Rhino command line
            RhinoApp.WriteLine(fullMessage);
            
            // Write to file
            WriteToFile(fileMessage);
        }

        private static void WriteToFile(string message)
        {
            if (!_fileLoggingEnabled || _logWriter == null)
                return;

            try
            {
                lock (_fileLock)
                {
                    _logWriter.WriteLine(message);
                }
            }
            catch
            {
                // Silently fail - don't crash plugin due to logging issues
            }
        }

        /// <summary>
        /// Closes the log file. Call on plugin unload.
        /// </summary>
        public static void Shutdown()
        {
            lock (_fileLock)
            {
                if (_logWriter != null)
                {
                    try
                    {
                        _logWriter.Flush();
                        _logWriter.Close();
                        _logWriter.Dispose();
                    }
                    catch { }
                    _logWriter = null;
                }
            }
        }
    }
}
