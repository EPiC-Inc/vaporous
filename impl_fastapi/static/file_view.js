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

function delete_file(filename) {
	if (CURRENT_DIRECTORY.length > 0) {
		filename = CURRENT_DIRECTORY + "/" + filename
	}
	console.log(filename);
	fetch(DELETE_URL, {
		method: "POST",
		headers: {"Content-Type": "application/json"},
		body: JSON.stringify([PUBLIC, filename])
	}).then(response => {
		response.json().then(json => {
			success = json[0]
			console.log(json);
			// TODO - re-compose?
			if (success) {
				window.location.reload();
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
