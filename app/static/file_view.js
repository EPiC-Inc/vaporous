var loading_dialog = document.getElementById("loading_dialog");

function refresh() {
	// Let the file system sync for slower systems
	// TODO - re-compose instead of reload?
	setTimeout(() => {
		loading_dialog.close();
		window.location.reload();
	}, 200);
}

function dragover(self, event) {
	event.preventDefault();
	event.stopPropagation();
	self.classList.add("dragging");
}
function dragover_files(self, event) {
	event.preventDefault();
	event.stopPropagation();
	if (!event.dataTransfer.types.includes("Files")) {
		return;
	}
	self.classList.add("dragging");
}
function dragleave(self, event) {
	event.preventDefault();
	event.stopPropagation();
	self.classList.remove("dragging");
}
function dragstart(self, event) {
	// event.preventDefault();
	event.stopPropagation();
	event.dataTransfer.setData("vaporous_data", self.getAttribute("path"));
}
function drop(self, event) {
	event.preventDefault();
	event.stopPropagation();
	self.classList.remove("dragging");

	let subject_path = event.dataTransfer.getData("vaporous_data");
	let target_path = self.getAttribute("path");
	if (!subject_path) {
		return;
	}
	if (subject_path == target_path) {
		return;
	} else {
		loading_dialog.show();
		fetch(MOVE_URL, {
			method: "POST",
			headers: {"Content-Type": "application/json"},
			body: JSON.stringify({
				file_path: subject_path,
				to: target_path,
				to_public: PUBLIC,
			})
		}).then(response => {
			response.json().then(json => {
				success = json[0];
				message = json[1];
				if (success) {
					refresh();
				} else {
					loading_dialog.close();
					alert(message);
				}
			});
		});
	}
}
function drop_files(self, event) {
	event.preventDefault();
	event.stopPropagation();
	self.classList.remove("dragging");
	event.dataTransfer.dropEffect = "copy";
	let files = event.dataTransfer.files;
	if (files.length < 1) {
		return;
	}
	loading_dialog.show();
	let upload_form = new FormData();
	upload_form.append("file_path", CURRENT_DIRECTORY);
	upload_form.append("to_public", PUBLIC);
	upload_form.append("compression_level", 0);
	for (var i = 0; i < files.length; i++) {
		upload_form.append("files", files[i]);
	}
	fetch(UPLOAD_URL, {
		method: "POST",
		body: upload_form
	}).then(response => {
		response.json().then(json => {
			console.log(json);
			refresh();
		});
	});
}

function create_new_folder() {
	let new_folder_name = prompt("New folder name?");
	if (new_folder_name) {
		loading_dialog.show();
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
					refresh();
				} else {
					loading_dialog.close();
					alert(message);
				}
			});
		});
	}
}

function rename(filename, new_name="") {
	new_name = prompt(`Rename ${filename} to?`);
	if (new_name) {
		loading_dialog.show();
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
					refresh();
				} else {
					loading_dialog.close();
					alert(message);
				}
			});
		});
	}
}

function upload_files() {
	loading_dialog.show();
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
			refresh();
		});
	});
}

function open_share_dialog(filepath, filename) {
	if (PUBLIC) {
		let share_url = PUBLIC_URL + "/" + filepath;
		document.getElementById("public_link").innerText = share_url.replace(" ", "%20");
		document.getElementById("public_share_dialog").showModal();
	} else {
		document.getElementById('share_form').reset();
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
	loading_dialog.show();
	let share_form_element = document.getElementById('share_form');
	let upload_form = new FormData(share_form_element);
	upload_form.append("file_path", document.getElementById("file_path_to_share").value);
	fetch(SHARE_URL, {
		method: "POST",
		body: upload_form
	}).then(response => {
		response.json().then(json => {
			success = json[0];
			message = json[1];
			loading_dialog.close();
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
	loading_dialog.show();
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
				refresh();
			} else {
				loading_dialog.close();
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
