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

	add_auth(config) {
		if (this.auth_token) {
			const res = { ...config };
			res.headers = { ...res.headers };
			res.headers['Authorization'] = `Bearer ${this.auth_token}`;
			return res;
		}
		return config;
	}

	http_request(method, path, body, config) {
		const fn = axios[method];
		const url = import.meta.env.VITE_BACKEND_URL + path;
		const conf = this.add_auth(config);
		return body === undefined? fn(url, conf): fn(url, body, conf);
	}

	get(path, config) { return this.http_request('get', path, undefined, config); }
	post(path, body, config) { return this.http_request('post', path, body, config); }
	patch(path, body, config) { return this.http_request('patch', path, body, config); }
	put(path, body, config) { return this.http_request('put', path, body, config); }
}

export const error_msg_list = err => {
	const obj_dfs = (list, pre, o) => {
		if (Array.isArray(o))
			o.forEach(v => obj_dfs(list, pre, v));
		else if (typeof o === 'object')
			Object.entries(o).forEach(([str, v]) => obj_dfs(list, pre + str + ' - ', v))
		else
			list.push(pre + o);
	}
	if (err.response) {
		const list = ['Error ' + err.status];
		obj_dfs(list, '-- ', err.response.data);
		return list;
	}
	return ['Failed: ' + err.message];
}
export const error_msg = err => {
	const nested = (obj, ...ms) => ms.reduce((a, m) => a && a[m], obj);

	const detail = nested(err, 'response', 'data', 'detail');
	const message = nested(err, 'response', 'data', 'payload', 'message', 0);

	if (detail)
		return 'Error ' + err.status + ': ' + detail
	else if (message)
		return 'Error ' + err.status + ': ' + message;
	else if (err.response)
		return 'Error ' + err.status;
	else
		return 'Failed: ' + err.message;
};

export const session = new Session;

const auth_data = JSON.parse(localStorage.getItem('auth-data'));
if (auth_data)
	session.set_creds(auth_data.username, auth_data.auth_token);
session.listen((username, auth_token) => localStorage.setItem('auth-data', JSON.stringify({ username, auth_token })));

export default session;
