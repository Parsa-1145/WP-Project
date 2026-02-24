import axios from 'axios'

class Session {
	activeUser = null;
	accounts ={};
	subs = [];

	login(username, password) {
		this.accounts[username] = { password };
		this.activeUser = username;
		this._notify();
	}


	switch_account(username) {
		if (this.accounts[username]) {
            this.activeUser = username;
            this._notify();
        }
	}

	logout(username = this.activeUser) {
        delete this.accounts[username];
        
        if (this.activeUser === username) {
            const remainingUsers = Object.keys(this.accounts);
            this.activeUser = remainingUsers.length > 0 ? remainingUsers[0] : null;
        }

		this._notify();
    }

	_notify() {
        for (const fn of this.subs) {
            fn(this.activeUser, this.accounts);
        }
    }

	listen(fn) {
		this.subs.push(fn)
		return () => this.subs = this.subs.filter(f => f !== fn);
	}

	_add_auth(config) {
		const auth_token = this.activeUser ? this.accounts[this.activeUser].password : null;
		if (auth_token) {
			const res = { ...config };
			res.headers = { ...res.headers };
			res.headers['Authorization'] = `Bearer ${auth_token}`;
			return res;
		}
		return config;
	}

	http_request(method, path, body, config) {
		const fn = axios[method];
		const url = import.meta.env.VITE_BACKEND_URL + path;
		const conf = this._add_auth(config);
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
if (auth_data && auth_data.accounts) {
	session.accounts = auth_data.accounts;
	session.activeUser = auth_data.activeUser;
}
session.listen((activeUser, accounts) => localStorage.setItem('auth-data', JSON.stringify({ activeUser, accounts })));

export default session;
