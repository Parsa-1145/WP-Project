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
		return () => this.subs = this.subs.filter(f => f !== fn);
	}

	_add_auth(config) {
		if (this.auth_token) {
			const res = { ...config };
			res.headers = { ...res.headers };
			res.headers['Authorization'] = `Bearer ${this.auth_token}`;
			return res;
		}
		return config;
	}

	get(path, config) { return axios.get(import.meta.env.VITE_BACKEND_URL + path, this._add_auth(config)); }
	post(path, body, config) { return axios.post(import.meta.env.VITE_BACKEND_URL + path, body, this._add_auth(config)); }
}

const session = new Session;

const auth_data = JSON.parse(localStorage.getItem('auth-data'));
if (auth_data)
	session.set_creds(auth_data.username, auth_data.auth_token);
session.listen((username, auth_token) => localStorage.setItem('auth-data', JSON.stringify({ username, auth_token })));

export default session;
