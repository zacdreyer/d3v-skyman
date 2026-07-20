using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Sockets;
using System.Security.Cryptography;
using System.Text;

namespace D3vSkymanClient;

public static class Program
{
    public static void Main(string[] args)
    {
        var client = new D3vSkymanClient(
            ExampleConfig.Host,
            ExampleConfig.Port,
            ExampleConfig.Password,
            ExampleConfig.Iv,
            ExampleConfig.Key
        );

        var response = client.SendCommand("CLI echo 'hello from C#' && echo 'streaming works';");
        Console.WriteLine(response.Result);
    }
}

public sealed class D3vSkymanClient
{
    private readonly string _host;
    private readonly int _port;
    private readonly string _password;
    private readonly EncryptionHandler _encryption;
    private readonly List<byte> _buffer = new();

    public D3vSkymanClient(string host, int port, string password, string iv, string key)
    {
        _host = host;
        _port = port;
        _password = password;
        _encryption = new EncryptionHandler(iv, key);
    }

    public CommandResult SendCommand(string command)
    {
        using var client = new TcpClient();
        client.Connect(_host, _port);
        using var stream = client.GetStream();

        var welcome = ReadFrame(stream);
        if (welcome is null)
        {
            return new CommandResult("failed", "No welcome response received.", string.Empty, new List<string>());
        }

        var welcomeText = _encryption.Decrypt(welcome);
        WriteFrame(stream, $"AUTH {_password};");

        var authFrame = ReadFrame(stream);
        if (authFrame is null)
        {
            return new CommandResult("failed", "No authentication response received.", string.Empty, new List<string>());
        }

        var authText = _encryption.Decrypt(authFrame);
        if (authText.Contains("Authentication failed", StringComparison.OrdinalIgnoreCase))
        {
            return new CommandResult("failed", authText, string.Empty, new List<string>());
        }

        WriteFrame(stream, command);

        var chunks = new List<string>();
        var result = new StringBuilder();

        while (true)
        {
            var frame = ReadFrame(stream);
            if (frame is null)
            {
                break;
            }

            var payload = _encryption.Decrypt(frame);
            if (payload == "STREAM_END")
            {
                break;
            }

            if (payload.StartsWith("STREAM_CHUNK:", StringComparison.Ordinal))
            {
                var chunk = payload.Substring("STREAM_CHUNK:".Length);
                result.Append(chunk);
                chunks.Add(chunk);
                continue;
            }

            result.Append(payload);
            chunks.Add(payload);
        }

        return new CommandResult("success", "Command successfully sent to server.", result.ToString(), chunks);
    }

    private void WriteFrame(NetworkStream stream, string message)
    {
        var payload = _encryption.Encrypt(message) + "\n";
        var bytes = Encoding.UTF8.GetBytes(payload);
        stream.Write(bytes, 0, bytes.Length);
    }

    private string? ReadFrame(NetworkStream stream)
    {
        while (true)
        {
            var newlineIndex = _buffer.IndexOf((byte) '\n');
            if (newlineIndex >= 0)
            {
                var frameBytes = _buffer.GetRange(0, newlineIndex);
                _buffer.RemoveRange(0, newlineIndex + 1);
                return Encoding.UTF8.GetString(frameBytes.ToArray()).TrimEnd('\r');
            }

            var buffer = new byte[8192];
            var read = stream.Read(buffer, 0, buffer.Length);
            if (read == 0)
            {
                if (_buffer.Count > 0)
                {
                    var leftover = Encoding.UTF8.GetString(_buffer.ToArray()).TrimEnd('\r');
                    _buffer.Clear();
                    return leftover;
                }

                return null;
            }

            _buffer.AddRange(buffer.Take(read));
        }
    }
}

public sealed class EncryptionHandler
{
    private readonly byte[] _iv;
    private readonly byte[] _key;
    private const int BlockSize = 16;

    public EncryptionHandler(string iv, string key)
    {
        _iv = Encoding.UTF8.GetBytes(iv);
        _key = Encoding.UTF8.GetBytes(key);
    }

    public string Encrypt(string data)
    {
        using var aes = Aes.Create();
        aes.Mode = CipherMode.CBC;
        aes.Padding = PaddingMode.None;
        aes.IV = _iv;
        aes.Key = _key;

        var padded = Pad(Encoding.UTF8.GetBytes(data));
        using var encryptor = aes.CreateEncryptor();
        var encrypted = encryptor.TransformFinalBlock(padded, 0, padded.Length);
        return Convert.ToBase64String(encrypted);
    }

    public string Decrypt(string data)
    {
        using var aes = Aes.Create();
        aes.Mode = CipherMode.CBC;
        aes.Padding = PaddingMode.None;
        aes.IV = _iv;
        aes.Key = _key;

        var bytes = Convert.FromBase64String(data);
        using var decryptor = aes.CreateDecryptor();
        var decrypted = decryptor.TransformFinalBlock(bytes, 0, bytes.Length);
        return Encoding.UTF8.GetString(Unpad(decrypted));
    }

    private static byte[] Pad(byte[] data)
    {
        var padding = BlockSize - (data.Length % BlockSize);
        var output = new byte[data.Length + padding];
        Buffer.BlockCopy(data, 0, output, 0, data.Length);
        for (var index = data.Length; index < output.Length; index++)
        {
            output[index] = (byte)padding;
        }

        return output;
    }

    private static byte[] Unpad(byte[] data)
    {
        if (data.Length == 0)
        {
            return Array.Empty<byte>();
        }

        var padding = data[^1];
        if (padding < 1 || padding > BlockSize)
        {
            return data;
        }

        var paddingLength = padding;
        if (paddingLength > data.Length)
        {
            return data;
        }

        for (var index = data.Length - paddingLength; index < data.Length; index++)
        {
            if (data[index] != padding)
            {
                return data;
            }
        }

        var output = new byte[data.Length - paddingLength];
        Buffer.BlockCopy(data, 0, output, 0, output.Length);
        return output;
    }
}

public sealed class CommandResult
{
    public CommandResult(string status, string message, string result, IReadOnlyList<string> stream)
    {
        Status = status;
        Message = message;
        Result = result;
        Stream = stream;
    }

    public string Status { get; }
    public string Message { get; }
    public string Result { get; }
    public IReadOnlyList<string> Stream { get; }
}
