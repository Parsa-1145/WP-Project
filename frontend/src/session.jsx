import axios from 'axios'

class Session {
	username;
	auth_token;
	subs = [];

	set_creds(username, auth_token) {
		for (const fn of this.subs)
			fn(username, auth_token);
		this.username = username;
		this.auth_token = auth_token;
	}

	listen(fn) {
		this.subs.push(fn)
		return () => this.subs = this.subs.filter(f => f === fn);
	}

	http_request(method, path, body0) {
		const body = { ...body0 };
		if (this.auth_token)
			body.headers = { ...body.headers, Authorization: `Bearer ${this.auth_token}` };

		return axios[method](import.meta.env.VITE_BACKEND_URL + path, body);
	}
	get(path) { return this.http_request('get', path); }
	post(path, body) { return this.http_request('post', path, body); }
}

const session = new Session;

const auth_data = JSON.parse(localStorage.getItem('auth-data'));
if (auth_data)
	session.set_creds(auth_data.username, auth_data.auth_token);
session.listen((username, auth_token) => localStorage.setItem('auth-data', JSON.stringify({ username, auth_token })));

export default session;
