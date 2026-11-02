/**
 * Crypto Bridge for TIM Sercomm Router API
 * Interacts with bundled Stanford Javascript Crypto Library (SJCL)
 */
const path = require("path");
const sjcl = require(path.join(__dirname, "sjcl.js"));

function main() {
    const action = process.argv[2];
    const arg1 = process.argv[3];
    const arg2 = process.argv[4];

    try {
        if (action === "derive_dk") {
            const password = arg1;
            const saltHex = arg2;
            const saltBits = sjcl.codec.hex.toBits(saltHex);
            const derivedKey = sjcl.misc.pbkdf2(password, saltBits, 1000, 128);
            process.stdout.write(sjcl.codec.hex.fromBits(derivedKey));
        } else if (action === "encrypt") {
            const dkHex = arg1;
            const plaintext = arg2;
            const iv = sjcl.random.randomWords(3, 0);
            const ciphertext = sjcl.encrypt(dkHex, plaintext, { iter: 1000, iv: iv });
            process.stdout.write(ciphertext);
        } else if (action === "decrypt") {
            const dkHex = arg1;
            const ctJson = arg2;
            const decrypted = sjcl.decrypt(dkHex, ctJson);
            process.stdout.write(decrypted);
        } else {
            process.stderr.write("Unknown action: " + action);
            process.exit(1);
        }
    } catch (err) {
        process.stderr.write("CryptoError: " + err.message);
        process.exit(2);
    }
}

main();
