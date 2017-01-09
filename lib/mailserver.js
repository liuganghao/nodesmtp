
/**
 * MailDev - mailserver.js
 */
// NOTE - simplesmtp is for backwards compatibility with 0.10.x
var simplesmtp = require('simplesmtp');
var SMTPServer = require('smtp-server').SMTPServer;
var MailParser = require('mailparser').MailParser;
var events = require('events');
var fs = require('fs');
var os = require('os');
var path = require('path');
var logger = require('./logger');
var outgoing = require('./outgoing');

var version = process.version.replace(/v/, '').split(/\./).map(function (n) { return parseInt(n, 10); });
var legacy = version[0] === 0 && version[1] <= 10;
var defaultPort = 25;
var defaultHost = '0.0.0.0';
var config = {};
var store = [];
var dircount = 0;
var filecount = 0;
var maxfilecount = 1024;
var tempDir = path.join(path.dirname(process.argv[1]), "../tmp", Date.now().toString());
var currnetTempDir = path.join(tempDir, dircount.toString());

var eventEmitter = new events.EventEmitter();
var smtp;

var cpoptions = {
    encoding: 'utf8',
    timeout: 0,
    maxBuffer: 200 * 1024,
    killSignal: 'SIGTERM',
    setsid: false,
    cwd: null,
    env: null
};

var cp = require('child_process');
var utilmobile = {
    checkMobile: function (telphone) {
        var isChinaMobile = /^134[0-8]\d{7}$|^(?:13[5-9]|147|15[0-27-9]|178|18[2-478])\d{8}$/; //移动方面最新答复
        var isChinaUnion = /^(?:13[0-2]|145|15[56]|176|18[56])\d{8}$/; //向联通微博确认并未回复
        var isChinaTelcom = /^(?:133|153|177|18[019])\d{8}$/; //1349号段 电信方面没给出答复，视作不存在
        var isOtherTelphone = /^170([059])\d{7}$/;//其他运营商
        telphone = telphone.trim()
        if (telphone.length !== 11) {
            return this.setReturnJson(false, '未检测到正确的手机号码');
        }
        else {
            if (isChinaMobile.test(telphone)) {
                return this.setReturnJson(true, '移动', { name: 'ChinaMobile' });
            }
            else if (isChinaUnion.test(telphone)) {
                return this.setReturnJson(true, '联通', { name: 'ChinaUnion' });
            }
            else if (isChinaTelcom.test(telphone)) {
                return this.setReturnJson(true, '电信', { name: 'ChinaTelcom' });
            }
            else if (isOtherTelphone.test(telphone)) {
                var num = isOtherTelphone.exec(telphone);
                return this.setReturnJson(true, '', { name: '' });
            }
            else {
                return this.setReturnJson(false, '未检测到正确的手机号码');
            }
        }
    },
    setReturnJson: function (status, msg, data) {
        if (typeof status !== 'boolean' && typeof status !== 'number') {
            status = false;
        }
        if (typeof msg !== 'string') {
            msg = '';
        }
        return {
            'status': status,
            'msg': msg,
            'data': data
        };
    }
}
/**
 * Mail Server exports
 */
var mailServer = module.exports = {};
/**
 * Create temp folder
 */
function createTempFolder() {

    if (fs.existsSync(currnetTempDir)) {
        clearTempFolder();
        return;
    }

    if (!fs.existsSync(path.dirname(currnetTempDir))) {
        fs.mkdirSync(path.dirname(currnetTempDir));
        logger.log('Temporary directory created at %s', path.dirname(currnetTempDir));
    }

    if (!fs.existsSync(currnetTempDir)) {
        fs.mkdirSync(currnetTempDir);
        logger.log('Temporary directory created at %s', currnetTempDir);
    }
}
function handleDataStream(stream, session, callback) {
    var phone = session.envelope.rcptTo[0].address.split('@')[0];
    var checkresult = utilmobile.checkMobile(phone);
    if (!checkresult.status) {
        logger.info(JSON.stringify(checkresult));
        return;
    }
    if (filecount > maxfilecount) {
        filecount = 0;
        dircount = dircount + 1;
        currnetTempDir = path.join(tempDir, dircount.toString());
        createTempFolder();
    }
    var id = Date.now() + "_" + phone;
    var chunklen = 0;
    var eml = fs.createWriteStream(path.join(currnetTempDir, id + '.eml'));
    logger.info('Start reciving file:' + eml.path.toString());
    stream.on('data', function (chunk) {
        chunklen += chunk.length;
        eml.write(chunk);
        //logger.info('< %s received %s bytes>',id, chunklen);
    }.bind(this));

    stream.on('end', function () {
        logger.info('number ' + filecount + ' Successed reciving file size:' + chunklen + " path:" + eml.path.toString());
        callback();
        cp.exec('python invoiceminer/emlintomysql.py '+eml.path.toString(), (e, stdout, stderr) => {
            if (!e) {
                logger.log(stdout);
                logger.error(stderr);
            }
            else {
                logger.error(e)
            }
        });
        filecount++;
    }.bind(this));
}
/**
 * Create and configure the mailserver
 */
mailServer.create = function (port, host, user, password) {

    // Start the server & Disable DNS checking
    if (legacy) {
        throw new Error("不支持nodejs版本：" + process.version)
    } else {
        smtp = new SMTPServer({
            incomingUser: user,
            incomingPassword: password,
            onAuth: authorizeUser,
            onData: handleDataStream,
            logger: false,
            disabledCommands: !!(user && password) ? ['STARTTLS'] : ['AUTH']
        });
    }

    // Setup temp folder for attachments
    createTempFolder();

    mailServer.port = port || defaultPort;
    mailServer.host = host || defaultHost;

    smtp.on('error',(err)=>{
        logger.error(err);
    });
};
/**
 * Start the mailServer
 */
mailServer.listen = function (callback) {

    if (typeof callback !== 'function') callback = null;

    // Listen on the specified port
    smtp.listen(mailServer.port, mailServer.host, function (err) {
        if (err) {
            if (callback) {
                callback(err);
            } else {
                throw err;
            }
        }

        if (callback) callback();

        logger.info('MailDev SMTP Server running at %s:%s', mailServer.host, mailServer.port);
    });
};

/**
 * Stop the mailserver
 */
mailServer.end = function (callback) {
    var method = legacy ? 'end' : 'close';
    smtp[method](callback);
    outgoing.close();
};
/**
 * Extend Event Emitter methods
 * events:
 *   'new' - emitted when new email has arrived
 */
mailServer.on = eventEmitter.on.bind(eventEmitter);
mailServer.emit = eventEmitter.emit.bind(eventEmitter);
mailServer.removeListener = eventEmitter.removeListener.bind(eventEmitter);
mailServer.removeAllListeners = eventEmitter.removeAllListeners.bind(eventEmitter);
//mailServer.error
/**
 * Authorize callback for smtp server
 */

function authorizeUser(auth, session, callback) {
    var username = auth.username;
    var password = auth.password;

    // conn, username, password, callback
    if (legacy) {
        username = arguments[1];
        password = arguments[2];
        callback = arguments[3];
    }

    if (this.options.incomingUser && this.options.incomingPassword) {
        if (username !== this.options.incomingUser ||
            password !== this.options.incomingPassword) {
            return callback(new Error('Invalid username or password'));
        }
    }
    callback(null, { user: this.options.incomingUser });
}
