import { WEBUI_API_BASE_URL } from '$lib/constants';

export const SaveUsageRate = async (token: string, called_model_name: string, called_model_version:string, user_prompt: string, model_ans: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/usagerate/save_usagerate`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		},
		body: JSON.stringify({
			called_model_name: called_model_name,
            called_model_version: called_model_version,
            user_prompt: user_prompt,
            model_ans: model_ans,
		}),
		signal: AbortSignal.timeout(5000)
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