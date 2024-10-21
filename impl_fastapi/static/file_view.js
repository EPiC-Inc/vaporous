function upload_files() {
	let upload_form_element = document.getElementById("upload_form");
	let upload_form = new FormData(upload_form_element);
	upload_form.append("file_path", CURRENT_DIRECTORY);
	//TODO
	upload_form.append("compression_level", 0);
	fetch(UPLOAD_URL, {
		method: "POST",
		body: upload_form
	}).then(response => {
		upload_form_element.reset();
		response.json().then(json => {
			console.log(json);
			// TODO - reload / re-compose
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
