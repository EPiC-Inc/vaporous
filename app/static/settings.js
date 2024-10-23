var loading_dialog = document.getElementById("loading_dialog");

function change_username() {
	let username_change_form = document.getElementById("username_change_form");
	loading_dialog.show();
	setTimeout(() => {
		loading_dialog.close();
	}, 1000);
}

function change_password() {
	document.getElementById("password_change_message").innerText = "";
	let password_change_form = document.getElementById("password_change_form");
	loading_dialog.show();
	fetch(PASSWORD_CHANGE_URL, {
		method: "POST",
		body: new FormData(password_change_form)
	}).then(response => {
	console.log("TEST2")
		response.json().then(json => {
			password_change_form.reset();
			let success = json[0];
			let message = json[1];
			console.log(success);
			console.log(message);
			loading_dialog.close();
			if (!success) {
				document.getElementById("password_change_message").innerText = message;
				document.getElementById("password_change").showModal();
			}
		});
	});
}
