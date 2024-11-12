import { WEBUI_API_BASE_URL } from '$lib/constants';

export const getResponses = async (token: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/responses/`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.log(err);
			error = err.detail;
			return null;
		});

	if (error) {
		throw error;
	}

	return res ? res : [];
};

export const SaveResponse = async (token: string, chat_id: string, message_id: string, feedback: string, userprompt: string, 
	model_ans: string, userselectreason: string, usercomment: string, used_model: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/responses/save_response`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		},
		body: JSON.stringify({
			chat_id: chat_id,
            message_id: message_id,
            feedback: feedback,
            userprompt: userprompt,
            model_ans: model_ans,
			userselectreason: userselectreason,
    		usercomment: usercomment,
			used_model: used_model
		})
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err;
			console.log(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const DeleteResponseById = async (token:string, id: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/responses/${id}`, {
		method: 'DELETE',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.then((json) => {
			return json;
		})
		.catch((err) => {
			error = err.detail;

			console.log(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};