function create_new_folder() {
	let new_folder_name = prompt("New folder name?");
	if (new_folder_name) {
		fetch(NEW_FOLDER_URL, {
			method: "POST",
			headers: {"Content-Type": "application/json"},
			body: JSON.stringify({
				file_path: CURRENT_DIRECTORY,
				folder_name: new_folder_name,
				to_public: PUBLIC,
			})
		}).then(response => {
			response.json().then(json => {
				success = json[0];
				message = json[1];
				if (success) {
					window.location.reload();
				} else {
					alert(message);
				}
			});
		});
	}
}

function rename(filename, new_name="") {
	new_name = prompt(`Rename ${filename} to?`);
	if (new_name) {
		if (CURRENT_DIRECTORY.length > 0) {
			filename = CURRENT_DIRECTORY + "/" + filename;
		}
		fetch(RENAME_URL, {
			method: "POST",
			headers: {"Content-Type": "application/json"},
			body: JSON.stringify({
				file_path: filename,
				new_name: new_name,
				to_public: PUBLIC,
			})
		}).then(response => {
			response.json().then(json => {
				success = json[0];
				message = json[1];
				if (success) {
					window.location.reload();
				} else {
					alert(message);
				}
			});
		});
	}
}

function upload_files() {
	let upload_form_element = document.getElementById("upload_form");
	let upload_form = new FormData(upload_form_element);
	upload_form.append("file_path", CURRENT_DIRECTORY);
	upload_form.append("to_public", PUBLIC);
	//TODO
	fetch(UPLOAD_URL, {
		method: "POST",
		body: upload_form
	}).then(response => {
		upload_form_element.reset();
		response.json().then(json => {
			console.log(json);
			// TODO - re-compose?
			window.location.reload();
		});
	});
}

function open_share_dialog(filepath, filename) {
	if (PUBLIC) {
		document.getElementById("public_link").innerText = PUBLIC_URL + "/" + filepath;
		document.getElementById("public_share_dialog").showModal();
	} else {
		document.getElementById("existing_shares").innerHTML = "Loading...";
		document.getElementById("file_path_to_share").value = filepath;
		fetch(LIST_SHARE_URL + "?filter=" + filepath, {
			method: "GET"
		}).then(response => {
			// upload_form_element.reset();
			response.json().then(json => {
				document.getElementById("name_to_share").innerText = filename;
				document.getElementById("existing_shares").innerHTML = "";
				if (json.length > 0) {
					json.forEach(share => {
						let child = document.createElement("a");
						child.classList.add("link");
						child.onclick = () => {
							navigator.clipboard.writeText(share.url);
						}
						child.innerText = share.id;
						document.getElementById("existing_shares").appendChild(child);
					});
				} else {
					document.getElementById("existing_shares").innerText = "None";
				}
				document.getElementById("share_dialog").showModal();
			});
		});
	}
}

function publish_share() {
	let filepath = document.getElementById("file_path_to_share").value;
	fetch(SHARE_URL, {
		method: "POST",
		body: filepath
	}).then(response => {
		// upload_form_element.reset();
		response.json().then(json => {
			success = json[0];
			message = json[1];
			if (success) {
				navigator.clipboard.writeText(message);
				open_share_dialog(
					document.getElementById("file_path_to_share").value,
					document.getElementById("name_to_share").innerText
				);
			} else {
				alert(message);
			}
		});
	});
}

function delete_file(filename, is_dir=false) {
	if (is_dir) {
		if (!confirm(filename + " is a directory! Delete anyway?")) {
			return;
		}
	}
	// TODO - make this use file path instead of file name??
	if (CURRENT_DIRECTORY.length > 0) {
		filename = CURRENT_DIRECTORY + "/" + filename;
	}
	console.log(filename);
	fetch(DELETE_URL, {
		method: "POST",
		headers: {"Content-Type": "application/json"},
		body: JSON.stringify({
			from_public: PUBLIC,
			file_path: filename
		})
	}).then(response => {
		response.json().then(json => {
			success = json[0];
			message = json[1];
			// TODO - re-compose?
			if (success) {
				window.location.reload();
			} else {
				alert(message);
			}
		});
	});
}

// function compose_files(path) {
// 	fetch(COMPOSER_URL, {
// 		method: "POST",
// 		headers: {"Content-Type": "application/json"},
// 		body: JSON.stringify({
// 			file_path: path,
// 			public: false
// 		})
// 	}).then(response => {
// 		response.text().then(text => {
// 			document.getElementById("file_container").innerHTML = text;
// 		});
// 	});
// }

// window.onload = () => {
// 	compose_files(".");
// }
