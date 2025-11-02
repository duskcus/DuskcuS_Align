<h1>Krita Plugin Installation Guide</h1>

<h2>Method 1: Using Krita's Resource Manager</h2>
<ol>
    <li>Open Krita</li>
    <li>Go to Settings > Manage Resources</li>
    <li>Click "Import Bundle/Resource"</li>
    <li>Select your plugin file</li>
    <li>Restart Krita</li>
</ol>

<h2>Method 2: Manual Installation</h2>
<ol>
    <li>Find Krita's resource folder:
        <ul>
            <li>Windows: %APPDATA%/krita</li>
            <li>macOS: ~/Library/Application Support/krita</li>
            <li>Linux: ~/.local/share/krita</li>
        </ul>
    </li>
    <li>Copy the plugin files to the "pykrita" folder</li>
    <li>Restart Krita</li>
    <li>Enable the plugin in Settings > Configure Krita > Python Plugin Manager</li>
</ol>

<h2>Troubleshooting</h2>
<ul>
    <li>Make sure you're using a compatible Krita version</li>
    <li>Check that Python scripting is enabled</li>
    <li>View Krita's log for error messages</li>
</ul>
