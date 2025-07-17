const { app } = require("electron");
const { BrowserWindow, screen, Menu, MenuItem } = require("electron");
const https = require("https");
const path = require("path");
const fs = require("fs");
const { exec } = require("child_process");
const { dialog } = require("electron");

const splits = __dirname.split("/");
const voichaiPath = splits.splice(0, splits.length - 2).join("/");

const checkInstallPath = voichaiPath.concat("/shell/voichai-checkInstall");
const installPath = voichaiPath.concat("/install");
const startPath = voichaiPath.concat("/shell/voichai-start");
const stopPath = voichaiPath.concat("/shell/voichai-stop");
// Access command-line arguments
const args = process.argv.slice(2);

// Additional setup for Electron app

const dockMenuTemplate = [
    {
        label: "File",
        submenu: [
            {
                label: "Custom",
                click() {
                    // Action to perform when the menu item is clicked
                    console.log("Custom option clicked");
                },
            },
            { type: "separator" },
            { role: "quit" },
        ],
    },
];
// Build the dock menu from the template
const dockMenu = Menu.buildFromTemplate(dockMenuTemplate);
// Set the application dock menu
app.dock.setMenu(dockMenu);

function runShellCommand(command) {
    return new Promise((resolve, reject) => {
        exec(command, (error, stdout, stderr) => {
            if (error) {
                reject({ error, stderr });
            } else {
                resolve(stdout);
            }
        });
    });
}

async function install() {
    const installCmd = "open ".concat(
        installPath,
        " && sleep 3 && ",
        checkInstallPath,
        " closed"
    );
    console.log("installCmd:", installCmd);
    return await runShellCommand(installCmd)
        .then((stdout) => {
            console.log("Output:", stdout);
            return 0;
        })
        .catch(async ({ error, stderr }) => {
            const options = {
                type: "error",
                message: `${installPath}`,
                detail: `${stderr}`,
                buttons: ["OK"],
            };
            await dialog.showMessageBox(options);
            return 1;
        });
}

async function checkInstall() {
    return await runShellCommand(checkInstallPath)
        .then((stdout) => {
            return 0;
        })
        .catch(async ({ error, stderr }) => {
            const options = {
                type: "info",
                message: "Checking dependences.",
                detail: `${stderr}`,
                buttons: ["Exit", "Install"],
            };
            const responses = await dialog.showMessageBox(options);
            if (responses.response === 0) {
                // Exit button pressed
                return -1;
            } else if (responses.response === 1) {
                // Install button pressed
                await install();
                return await checkInstall();
            }
            return -2;
        });
}

async function runShellCommandDialog(command) {
    await runShellCommand(command)
        .then((stdout) => {
            console.log("Output:", `${stdout}`);
            return;
        })
        .catch(async ({ error, stderr }) => {
            const options = {
                type: "error",
                message: `${command}`,
                detail: `${stderr}`,
                buttons: ["OK"],
            };
            await dialog.showMessageBox(options);
            return;
        });
}

async function startServer() {
    await runShellCommandDialog(startPath);
}

async function stopServer() {
    await runShellCommandDialog(stopPath);
}

const NODE_ENV = process.env.NODE_ENV;

function createWindow(url = "http://localhost:3999/") {
    const { width, height } = screen.getPrimaryDisplay().workAreaSize;
    const mainWindow = new BrowserWindow({
        width: width,
        height: height,
        webPreferences: {
            preload: path.join(__dirname, "preload.js"),
        },
    });

    mainWindow.loadURL(url);
    if (NODE_ENV === "development") {
        mainWindow.webContents.openDevTools();
    }
}

async function handleShutdown() {
    await stopServer();
}

function setDockMenu() {
    // Get the existing menu items
    const dockMenu = app.dock.getMenu();
    // Add a new option to the dock menu
    dockMenu.append(
        new MenuItem({
            label: "Open a new Window",
            click() {
                createWindow();
                // Action to be performed when the new menu item is clicked
            },
        })
    );

    // Set the updated dock menu
    app.dock.setMenu(dockMenu);
}

app.whenReady().then(async () => {
    setDockMenu();
    const res = await checkInstall();
    if (res !== 0) {
        app.quit();
    } else {
        await startServer();
        if (args.length > 0) {
            createWindow(args[0]);
        } else {
            createWindow();
        }
        app.on("activate", function () {
            if (BrowserWindow.getAllWindows().length === 0) {
                createWindow();
            }
        });
    }
});

app.on("before-quit", async (event) => {
    await handleShutdown();
});

app.on("window-all-closed", async () => {
    if (process.platform !== "darwin") {
        app.quit();
    }
});
