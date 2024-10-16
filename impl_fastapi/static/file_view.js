let compose_files = function(path) {
	fetch(COMPOSER_URL, {
		method: "POST",
		headers: {"Content-Type": "application/json"},
		body: JSON.stringify({
			file_path: path,
			public: false
		})
	}).then(response => {
		response.text().then(text => {
			document.getElementById("file_container").innerHTML = text;
		});
	});
}

window.onload = () => {
	compose_files(".");
}