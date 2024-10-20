var loading_dialog = document.getElementById("loading_dialog");

function change_username() {
	let username_change_form = document.getElementById("username_change_form");
	loading_dialog.show();
	setTimeout(() => {
		loading_dialog.close();
	}, 1000);
}

function change_password() {
	let password_change_form = document.getElementById("password_change_form");
	loading_dialog.show();
	setTimeout(() => {
		loading_dialog.close();
	}, 1000);
}
