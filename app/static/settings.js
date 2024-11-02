var loading_dialog = document.getElementById("loading_dialog");

function change_username() {
	loading_dialog.show();
	let username_change_form = document.getElementById("username_change_form");
	document.getElementById("username_change_message").innerText = "";
	fetch(USERNAME_CHANGE_URL, {
		method: "POST",
		body: new FormData(username_change_form)
	}).then(response => {
		response.json().then(json => {
			username_change_form.reset();
			let success = json[0];
			let message = json[1];
			console.log(success);
			console.log(message);
			loading_dialog.close();
			if (success) {
				window.location.reload();
			} else {
				document.getElementById("username_change_message").innerText = message;
				document.getElementById("username_change").showModal();
			}
		});
	});
}

function change_password() {
	document.getElementById("password_change_message").innerText = "";
	let password_change_form = document.getElementById("password_change_form");
	loading_dialog.show();
	fetch(PASSWORD_CHANGE_URL, {
		method: "POST",
		body: new FormData(password_change_form)
	}).then(response => {
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

function add_password() {
	document.getElementById("password_change_message").innerText = "";
	let password_add_form = document.getElementById("password_add_form");
	loading_dialog.show();
	fetch(PASSWORD_ADD_URL, {
		method: "POST",
		body: new FormData(password_add_form)
	}).then(response => {
		response.json().then(json => {
			password_add_form.reset();
			let success = json[0];
			let message = json[1];
			console.log(success);
			console.log(message);
			loading_dialog.close();
			if (!success) {
				document.getElementById("password_add_message").innerText = message;
				document.getElementById("password_add").showModal();
			}
		});
	});
}

function remove_password() {
	if (!confirm("Remove your password? Note: Any devices without passkeys will be difficult to set up!")) {
		return;
	}
	loading_dialog.show();
	fetch(PASSWORD_REMOVE_URL, {
		method: "POST",
	}).then(response => {
		response.json().then(json => {
			let success = json[0];
			let message = json[1];
			loading_dialog.close();
			if (!success) {
				alert("Error: " + message);
			}
		});
	});
}

function get_shares() {
	document.getElementById("existing_shares").innerHTML = "Loading...";
	fetch(LIST_SHARE_URL, {
		method: "GET"
	}).then(response => {
		// upload_form_element.reset();
		response.json().then(json => {
			document.getElementById("existing_shares").innerHTML = "";
			if (json.length > 0) {
				json.forEach(share => {
					let child = document.createElement("div");
					let child_link = document.createElement("a");
					let child_filename = document.createElement("a");
					let child_unshare = document.createElement("button");
					child_link.classList.add("link");
					child_link.onclick = () => {
						navigator.clipboard.writeText(share.url);
					}
					let info = "";
					if (share.collaborative) {
						info = "(Collab) "
					} else if (share.anonymous_access) {
						info = "(Anon) "
					}
					child_link.innerText = info + share.id;
					child.appendChild(child_link);

					child_filename.classList.add("link");
					child_filename.innerText = share.shared_filename;
					child_filename.title = share.shared_file;
					child_filename.href = FILE_URL + "/" + share.shared_file;
					child.appendChild(child_filename);

					child_unshare.classList.add("unshare_button");
					child_unshare.innerText = "Unshare";
					child_unshare.onclick = () => {unshare(share.id);};
					child.appendChild(child_unshare);

					document.getElementById("existing_shares").appendChild(child);
				});
			} else {
				document.getElementById("existing_shares").innerText = "None";
			}
		});
	});
}

function unshare(share_id) {
	fetch(DELETE_SHARE_URL, {
		method: "POST",
		body: share_id
	}).then(response => {
		response.json().then(json => {
			success = json[0];
			message = json[1];
			console.log(json);
			if (success) {
				get_shares();
			} else {
				alert(message);
			}
		});
	});
}

window.onload = () => {
	get_shares();
}
