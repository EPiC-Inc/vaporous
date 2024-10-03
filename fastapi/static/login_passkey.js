// Implementation details: https://webauthn.guide/#webauthn-api

function request_passkey_challenge() {
    fetch(CHALLENGE_URL)
    .then(response => response.text())
    .then(challenge_data => {
        const publicKeyCredentialRequestOptions = {
            challenge: Uint8Array.from(
                challenge_data, c => c.charCodeAt(0)),
            // allowCredentials: [{
            //     id: Uint8Array.from(
            //         credentialId, c => c.charCodeAt(0)),
            //     type: 'public-key',
            //     transports: ["usb", "nfc", "ble", "smart-card", "hybrid", "internal"],
            // }],
            timeout: 60000,
        }

        navigator.credentials.get({
            publicKey: publicKeyCredentialRequestOptions
        }).then(assertion => {console.log(assertion)});
    });
}

async function request_passkey() {
    const credential = await navigator.credentials.get({
        publicKey: publicKeyCredentialRequestOptions
    });
}
