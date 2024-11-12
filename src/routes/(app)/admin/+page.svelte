<script>
	import { WEBUI_BASE_URL } from '$lib/constants';
	import { WEBUI_NAME, config, user, showSidebar } from '$lib/stores';
	import { goto } from '$app/navigation';
	import { onMount, getContext } from 'svelte';

	import dayjs from 'dayjs';
	import relativeTime from 'dayjs/plugin/relativeTime';
	dayjs.extend(relativeTime);

	import { toast } from 'svelte-sonner';

	import { updateUserRole, getUsers, deleteUserById, updateUserModelWhitelistingdepartment, 
		updateUserModelWhitelisting, updateListUserModelWhitelisting, clearListUserModel} from '$lib/apis/users';

	import EditUserModal from '$lib/components/admin/EditUserModal.svelte';
	import Pagination from '$lib/components/common/Pagination.svelte';
	import ChatBubbles from '$lib/components/icons/ChatBubbles.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import UserChatsModal from '$lib/components/admin/UserChatsModal.svelte';
	import AddUserModal from '$lib/components/admin/AddUserModal.svelte';
	import ConfirmDialog from '$lib/components/common/ConfirmDialog.svelte';
	import Badge from '$lib/components/common/Badge.svelte';
	import Plus from '$lib/components/icons/Plus.svelte';
	import ChevronUp from '$lib/components/icons/ChevronUp.svelte';
	import ChevronDown from '$lib/components/icons/ChevronDown.svelte';
	import About from '$lib/components/chat/Settings/About.svelte';
	import UserModelSelect from '$lib/components/admin/Settings/UserModelSelect.svelte';
	import ListUserModelSelect from '$lib/components/admin/Settings/ListUserModelSelect.svelte';
	import { models } from '$lib/stores';

	const i18n = getContext('i18n');

	let loaded = false;
	let tab = '';
	let users = [];

	let search = '';
	let selectedUser = null;

	let page = 1;

	let showDeleteConfirmDialog = false;
	let showAddUserModal = false;

	let showUserChatsModal = false;
	let showEditUserModal = false;
	let showUserModelSelect = false;
	let showListUserModelSelect = false;
	let listUserid = [];

	console.log($models);
	let TotalModel = $models.map((model, index) => ({index: index, model_id: extractBeforeColon(model.id), selected: false}));

	function extractBeforeColon(inputString) {
		const colonIndex = inputString.indexOf(":");
		if (colonIndex !== -1) {
			return inputString.substring(0, colonIndex);
		}else {
			return inputString
		}
	}
	const updateRoleHandler = async (id, role) => {
		const res = await updateUserRole(localStorage.token, id, role).catch((error) => {
			toast.error(error);
			return null;
		});

		if (res) {
			users = await getUsers(localStorage.token);
		}
	};

	const editUserPasswordHandler = async (id, password) => {
		const res = await deleteUserById(localStorage.token, id).catch((error) => {
			toast.error(error);
			return null;
		});
		if (res) {
			users = await getUsers(localStorage.token);
			toast.success($i18n.t('Successfully updated.'));
		}
	};

	const deleteUserHandler = async (id) => {
		const res = await deleteUserById(localStorage.token, id).catch((error) => {
			toast.error(error);
			return null;
		});
		if (res) {
			users = await getUsers(localStorage.token);
		}
	};
	//更新模型名單請求
	const UpdateUserModelWhitelistingDepartmentHandler = async (id, model_selector, department) => {
		const res = await updateUserModelWhitelistingdepartment(localStorage.token, id, model_selector, department).catch((error) => {
			toast.error(error);
			return null;
		});
		if (res){
			users = await getUsers(localStorage.token);
			toast.success($i18n.t('Successfully Edit.'));
		}
	}
	//關閉編輯使用者模型頁面，並做存檔的動作
	const SaveSelectModel = async (id, model_selector) => {
		showUserModelSelect = false;
		const res = await updateUserModelWhitelisting(localStorage.token, id, model_selector).catch((error) => {
			toast.error(error);
			return null;
		});
		if (res){
			users = await getUsers(localStorage.token);
			toast.success($i18n.t('Successfully Edit.'));
		}
	}
	//更新列表中的使用者的可用模型。(若有使用搜尋，只會更新被搜尋到的使用者)
	const SaveListUserModel = async (listUserid, listselect) => {
		showListUserModelSelect = false;
		for (const element of TotalModel){
            element.selected = false;
        }
		if (listselect == ''){
			toast.error($i18n.t("Please reselect the model to share with users in the list."));
			return null;
		}
		// console.log(listselect);
		const res = await updateListUserModelWhitelisting(localStorage.token, listUserid, listselect).catch((error) => {
			toast.error(error);
			return null;
		});
		if (res){
			users = await getUsers(localStorage.token);
			toast.success($i18n.t('Successfully Edit.'));
		}
	}
	//清除列表人員可使用的模型名單。
	const ClearListUserModel = async (listUserid) => {
		showListUserModelSelect = false;
		for (const element of TotalModel){
            element.selected = false;
        }
		const res = await clearListUserModel(localStorage.token, listUserid, '').catch((error) => {
			toast.error(error);
			return null;
		});
		if (res){
			users = await getUsers(localStorage.token);
			toast.success($i18n.t('Successfully Edit.'));
		}
	}

	const UpdateListUserId = async (search) => {
		listUserid = [];
		users = await getUsers(localStorage.token);
		{users.forEach(user => {
			if (search === '') {
							listUserid.push(user.id);
						} else {
							let name = user.name.toLowerCase();
							const query = search.toLowerCase();
							//新增搜尋欄位，使用者的部門也能夠搜尋。
							if (name.includes(query) || user.department.toLowerCase().includes(query) || user.model_selector.toLowerCase().includes(query)){
								listUserid.push(user.id);
							}
						}
		});}
		return listUserid;
	}
	onMount(async () => {
		if ($user?.role !== 'admin') {
			await goto('/');
		} else {
			users = await getUsers(localStorage.token);
		}
		loaded = true;
	});
	let sortKey = 'created_at'; // default sort key
	let sortOrder = 'asc'; // default sort order

	function setSortKey(key) {
		if (sortKey === key) {
			sortOrder = sortOrder === 'asc' ? 'desc' : 'asc';
		} else {
			sortKey = key;
			sortOrder = 'asc';
		}
	}

	let filteredUsers;

	$: filteredUsers = users
		.filter((user) => {
			if (search === '') {
				return true;
			} else {
				let name = user.name.toLowerCase();
				const query = search.toLowerCase();
				return name.includes(query) || user.department.toLowerCase().includes(query) || user.model_selector.toLowerCase().includes(query);
			}
		})
		.sort((a, b) => {
			if (a[sortKey] < b[sortKey]) return sortOrder === 'asc' ? -1 : 1;
			if (a[sortKey] > b[sortKey]) return sortOrder === 'asc' ? 1 : -1;
			return 0;
		})
		.slice((page - 1) * 20, page * 20);
</script>

<ConfirmDialog
	bind:show={showDeleteConfirmDialog}
	on:confirm={() => {
		deleteUserHandler(selectedUser.id);
	}}
/>

{#key selectedUser}
	<EditUserModal
		bind:show={showEditUserModal}
		{selectedUser}
		sessionUser={$user}
		on:save={async () => {
			users = await getUsers(localStorage.token);
		}}
	/>
{/key}

<AddUserModal
	bind:show={showAddUserModal}
	on:save={async () => {
		users = await getUsers(localStorage.token);
	}}
/>
<UserChatsModal bind:show={showUserChatsModal} user={selectedUser} />
<UserModelSelect bind:show={showUserModelSelect} TotalModel={TotalModel} user={selectedUser} SaveSelectModel={SaveSelectModel}/>
<ListUserModelSelect bind:show={showListUserModelSelect} searchString={search} TotalModel={TotalModel} SaveListUserModel={SaveListUserModel} ClearListUserModel={ClearListUserModel} listUserid={listUserid}/>
{#if loaded}
	<div class="mt-0.5 mb-2 gap-1 flex flex-col md:flex-row justify-between">
		<div class="flex md:self-center text-lg font-medium px-0.5">
			{$i18n.t('Users')}
			<div class="flex self-center w-[1px] h-6 mx-2.5 bg-gray-50 dark:bg-gray-850" />

			<span class="text-lg font-medium text-gray-500 dark:text-gray-300">{users.length}</span>
			<Tooltip content={$i18n.t('Update List User Enable_model')}>
				<button
					class="self-center w-fit text-sm px-2 py-2 hover:bg-black/5 dark:hover:bg-white/5 rounded-xl"
						on:click={async () =>{
							showListUserModelSelect = !showListUserModelSelect;
							UpdateListUserId(search);
						}}
					>
					<div class=" m-auto self-center">
						<svg
							xmlns="http://www.w3.org/2000/svg"
							viewBox="0 0 20 20"
							fill="currentColor"
							class="w-5 h-5"
						>
							<path
								d="M5.433 13.917l1.262-3.155A4 4 0 017.58 9.42l6.92-6.918a2.121 2.121 0 013 3l-6.92 6.918c-.383.383-.84.685-1.343.886l-3.154 1.262a.5.5 0 01-.65-.65z"
							/>
							<path
								d="M3.5 5.75c0-.69.56-1.25 1.25-1.25H10A.75.75 0 0010 3H4.75A2.75 2.75 0 002 5.75v9.5A2.75 2.75 0 004.75 18h9.5A2.75 2.75 0 0017 15.25V10a.75.75 0 00-1.5 0v5.25c0 .69-.56 1.25-1.25 1.25h-9.5c-.69 0-1.25-.56-1.25-1.25v-9.5z"
							/>
						</svg>
					</div>
				</button>
			</Tooltip>
		</div>

		<div class="flex gap-1">
			<dic class="flex gap-0.5 text-gray-400 text-xs mr-15 mt-5">
				{$i18n.t("Model names should be separated by commas (',')")}
			</dic>
			<div class=" flex w-full space-x-2">
				<div class="flex flex-1">
					<div class=" self-center ml-1 mr-3">
						<svg
							xmlns="http://www.w3.org/2000/svg"
							viewBox="0 0 20 20"
							fill="currentColor"
							class="w-4 h-4"
						>
							<path
								fill-rule="evenodd"
								d="M9 3.5a5.5 5.5 0 100 11 5.5 5.5 0 000-11zM2 9a7 7 0 1112.452 4.391l3.328 3.329a.75.75 0 11-1.06 1.06l-3.329-3.328A7 7 0 012 9z"
								clip-rule="evenodd"
							/>
						</svg>
					</div>
					<input
						class=" w-full text-sm pr-4 py-1 rounded-r-xl outline-none bg-transparent"
						bind:value={search}
						placeholder={$i18n.t('Search')}
					/>
				</div>

				<div>
					<Tooltip content={$i18n.t('Add User')}>
						<button
							class=" p-2 rounded-xl hover:bg-gray-100 dark:bg-gray-900 dark:hover:bg-gray-850 transition font-medium text-sm flex items-center space-x-1"
							on:click={() => {
								showAddUserModal = !showAddUserModal;
							}}
						>
							<Plus className="size-3.5" />
						</button>
					</Tooltip>
				</div>
			</div>
		</div>
	</div>

	<div
		class="scrollbar-hidden relative whitespace-nowrap overflow-x-auto max-w-full rounded pt-0.5"
	>
		<table
			class="w-full text-sm text-left text-gray-500 dark:text-gray-400 table-auto max-w-full rounded"
		>
			<thead
				class="text-xs text-gray-700 uppercase bg-gray-50 dark:bg-gray-850 dark:text-gray-400 -translate-y-0.5"
			>
				<tr class="">
					<th
						scope="col"
						class="px-3 py-1.5 cursor-pointer select-none"
						on:click={() => setSortKey('role')}
					>
						<div class="flex gap-1.5 items-center">
							{$i18n.t('Role')}

							{#if sortKey === 'role'}
								<span class="font-normal"
									>{#if sortOrder === 'asc'}
										<ChevronUp className="size-2" />
									{:else}
										<ChevronDown className="size-2" />
									{/if}
								</span>
							{:else}
								<span class="invisible">
									<ChevronUp className="size-2" />
								</span>
							{/if}
						</div>
					</th>
					<th
						scope="col"
						class="px-3 py-1.5 cursor-pointer select-none"
						on:click={() => setSortKey('department')}
					>
						<div class="flex gap-1.5 items-center">
							{$i18n.t('department')}

							{#if sortKey === 'department'}
								<span class="font-normal"
									>{#if sortOrder === 'asc'}
										<ChevronUp className="size-2" />
									{:else}
										<ChevronDown className="size-2" />
									{/if}
								</span>
							{:else}
								<span class="invisible">
									<ChevronUp className="size-2" />
								</span>
							{/if}
						</div>
					</th>
					<th
						scope="col"
						class="px-3 py-1.5 cursor-pointer select-none"
						on:click={() => setSortKey('name')}
					>
						<div class="flex gap-1.5 items-center">
							{$i18n.t('Name')}

							{#if sortKey === 'name'}
								<span class="font-normal"
									>{#if sortOrder === 'asc'}
										<ChevronUp className="size-2" />
									{:else}
										<ChevronDown className="size-2" />
									{/if}
								</span>
							{:else}
								<span class="invisible">
									<ChevronUp className="size-2" />
								</span>
							{/if}
						</div>
					</th>
					<th
						scope="col"
						class="px-3 py-1.5 cursor-pointer select-none"
						on:click={() => setSortKey('email')}
					>
						<div class="flex gap-1.5 items-center">
							{$i18n.t('Email')}

							{#if sortKey === 'email'}
								<span class="font-normal"
									>{#if sortOrder === 'asc'}
										<ChevronUp className="size-2" />
									{:else}
										<ChevronDown className="size-2" />
									{/if}
								</span>
							{:else}
								<span class="invisible">
									<ChevronUp className="size-2" />
								</span>
							{/if}
						</div>
					</th>

					<th
						scope="col"
						class="px-3 py-1.5 cursor-pointer select-none"
						on:click={() => setSortKey('last_active_at')}
					>
						<div class="flex gap-1.5 items-center">
							{$i18n.t('Last Active')}

							{#if sortKey === 'last_active_at'}
								<span class="font-normal"
									>{#if sortOrder === 'asc'}
										<ChevronUp className="size-2" />
									{:else}
										<ChevronDown className="size-2" />
									{/if}
								</span>
							{:else}
								<span class="invisible">
									<ChevronUp className="size-2" />
								</span>
							{/if}
						</div>
					</th>
					<th
						scope="col"
						class="px-3 py-1.5 cursor-pointer select-none"
						on:click={() => setSortKey('created_at')}
					>
						<div class="flex gap-1.5 items-center">
							{$i18n.t('Created at')}
							{#if sortKey === 'created_at'}
								<span class="font-normal"
									>{#if sortOrder === 'asc'}
										<ChevronUp className="size-2" />
									{:else}
										<ChevronDown className="size-2" />
									{/if}
								</span>
							{:else}
								<span class="invisible">
									<ChevronUp className="size-2" />
								</span>
							{/if}
						</div>
					</th>

					<th
						scope="col"
						class="px-3 py-1.5 cursor-pointer select-none"
						on:click={() => setSortKey('oauth_sub')}
					>
						<div class="flex gap-1.5 items-center">
							{$i18n.t('OAuth ID')}

							{#if sortKey === 'oauth_sub'}
								<span class="font-normal"
									>{#if sortOrder === 'asc'}
										<ChevronUp className="size-2" />
									{:else}
										<ChevronDown className="size-2" />
									{/if}
								</span>
							{:else}
								<span class="invisible">
									<ChevronUp className="size-2" />
								</span>
							{/if}
						</div>
					</th>
					<th
						scope="col"
						class="px-3 py-1.5 cursor-pointer select-none"
						on:click={() => setSortKey('User_Model_Whitelisting')}
					>
						<div class="flex gap-1.5 items-center">
							{$i18n.t('User_Model_Whitelisting')}

							{#if sortKey === 'User_Model_Whitelisting'}
								<span class="font-normal"
									>{#if sortOrder === 'asc'}
										<ChevronUp className="size-2" />
									{:else}
										<ChevronDown className="size-2" />
									{/if}
								</span>
							{:else}
								<span class="invisible">
									<ChevronUp className="size-2" />
								</span>
							{/if}
						</div>
					</th>

					<th scope="col" class="px-3 py-2 text-right" />
				</tr>
			</thead>
			<tbody class="">
				{#each filteredUsers as user, userIdx}
					<tr class="bg-white dark:bg-gray-900 dark:border-gray-850 text-xs">
						<td class="px-3 py-1 min-w-[7rem] w-28">
							<button
								class=" translate-y-0.5"
								on:click={() => {
									if (user.role === 'user') {
										updateRoleHandler(user.id, 'admin');
									} else if (user.role === 'pending') {
										updateRoleHandler(user.id, 'user');
									} else {
										updateRoleHandler(user.id, 'pending');
									}
								}}
							>
								<Badge
									type={user.role === 'admin' ? 'info' : user.role === 'user' ? 'success' : 'muted'}
									content={$i18n.t(user.role)}
								/>
							</button>
						</td>

						<td class=" px-3 py-1">
							<input bind:value={user.department} placeholder={'FT-User' + (user.department ?? '')}/>
						</td>

						<td class="px-3 py-1 font-medium text-gray-900 dark:text-white w-max">
							<div class="flex flex-row w-max">
								<img
									class=" rounded-full w-6 h-6 object-cover mr-2.5"
									src={user.profile_image_url.startsWith(WEBUI_BASE_URL) ||
									user.profile_image_url.startsWith('https://www.gravatar.com/avatar/') ||
									user.profile_image_url.startsWith('data:')
										? user.profile_image_url
										: `/user.png`}
									alt="user"
								/>

								<div class=" font-medium self-center">{user.name}</div>
							</div>
						</td>
						<td class=" px-3 py-1"> {user.email} </td>

						<td class=" px-3 py-1">
							{dayjs(user.last_active_at * 1000).fromNow()}
						</td>

						<td class=" px-3 py-1">
							{dayjs(user.created_at * 1000).format($i18n.t('MMMM DD, YYYY'))}
						</td>

						<td class=" px-3 py-1"> {user.oauth_sub ?? ''} </td>

						<td class=" px-3 py-2" >
							<input bind:value={user.model_selector} style="background-color:white;color:black;font-size: 0.8rem;" placeholder={'Default value: ' + (user.model_selector ?? '')}/>
						</td>

						<td class="px-3 py-1 text-right">
							<div class="flex justify-end w-full">
								{#if $config.features.enable_admin_chat_access && user.role !== 'admin'}
									<Tooltip content={$i18n.t('SaveModelWhitelisting&department')}>
										<button
											class="self-center w-fit text-sm px-2 py-2 hover:bg-black/5 dark:hover:bg-white/5 rounded-xl"
											on:click={async () =>{
												UpdateUserModelWhitelistingDepartmentHandler(user.id, user.model_selector, user.department);
											}}
										>
										<div class=" m-auto self-center">
											<svg
												xmlns="http://www.w3.org/2000/svg"
												viewBox="0 0 20 20"
												fill="currentColor"
												class="w-5 h-5"
											>
												<path
													d="M5.433 13.917l1.262-3.155A4 4 0 017.58 9.42l6.92-6.918a2.121 2.121 0 013 3l-6.92 6.918c-.383.383-.84.685-1.343.886l-3.154 1.262a.5.5 0 01-.65-.65z"
												/>
												<path
													d="M3.5 5.75c0-.69.56-1.25 1.25-1.25H10A.75.75 0 0010 3H4.75A2.75 2.75 0 002 5.75v9.5A2.75 2.75 0 004.75 18h9.5A2.75 2.75 0 0017 15.25V10a.75.75 0 00-1.5 0v5.25c0 .69-.56 1.25-1.25 1.25h-9.5c-.69 0-1.25-.56-1.25-1.25v-9.5z"
												/>
											</svg>
										</div>
										</button>
									</Tooltip>
									<Tooltip content={$i18n.t('EditUserModel')}>
										<button
											class="self-center w-fit text-sm px-2 py-2 hover:bg-black/5 dark:hover:bg-white/5 rounded-xl"
											on:click={async () => {
												showUserModelSelect = !showUserModelSelect;
												selectedUser = user;
											}}
										>
										<div class=" m-auto self-center">
											<svg
												xmlns="http://www.w3.org/2000/svg"
												viewBox="0 0 20 20"
												fill="currentColor"
												class="w-5 h-5"
											>
												<path
													d="M5.433 13.917l1.262-3.155A4 4 0 017.58 9.42l6.92-6.918a2.121 2.121 0 013 3l-6.92 6.918c-.383.383-.84.685-1.343.886l-3.154 1.262a.5.5 0 01-.65-.65z"
												/>
												<path
													d="M3.5 5.75c0-.69.56-1.25 1.25-1.25H10A.75.75 0 0010 3H4.75A2.75 2.75 0 002 5.75v9.5A2.75 2.75 0 004.75 18h9.5A2.75 2.75 0 0017 15.25V10a.75.75 0 00-1.5 0v5.25c0 .69-.56 1.25-1.25 1.25h-9.5c-.69 0-1.25-.56-1.25-1.25v-9.5z"
												/>
											</svg>
										</div>
										</button>
									</Tooltip>
									<Tooltip content={$i18n.t('Chats')}>
										<button
											class="self-center w-fit text-sm px-2 py-2 hover:bg-black/5 dark:hover:bg-white/5 rounded-xl"
											on:click={async () => {
												showUserChatsModal = !showUserChatsModal;
												selectedUser = user;
											}}
										>
											<ChatBubbles />
										</button>
									</Tooltip>
								{/if}

								<Tooltip content={$i18n.t('Edit User')}>
									<button
										class="self-center w-fit text-sm px-2 py-2 hover:bg-black/5 dark:hover:bg-white/5 rounded-xl"
										on:click={async () => {
											showEditUserModal = !showEditUserModal;
											selectedUser = user;
										}}
									>
										<svg
											xmlns="http://www.w3.org/2000/svg"
											fill="none"
											viewBox="0 0 24 24"
											stroke-width="1.5"
											stroke="currentColor"
											class="w-4 h-4"
										>
											<path
												stroke-linecap="round"
												stroke-linejoin="round"
												d="m16.862 4.487 1.687-1.688a1.875 1.875 0 1 1 2.652 2.652L6.832 19.82a4.5 4.5 0 0 1-1.897 1.13l-2.685.8.8-2.685a4.5 4.5 0 0 1 1.13-1.897L16.863 4.487Zm0 0L19.5 7.125"
											/>
										</svg>
									</button>
								</Tooltip>

								{#if user.role !== 'admin'}
									<Tooltip content={$i18n.t('Delete User')}>
										<button
											class="self-center w-fit text-sm px-2 py-2 hover:bg-black/5 dark:hover:bg-white/5 rounded-xl"
											on:click={async () => {
												showDeleteConfirmDialog = true;
												selectedUser = user;
											}}
										>
											<svg
												xmlns="http://www.w3.org/2000/svg"
												fill="none"
												viewBox="0 0 24 24"
												stroke-width="1.5"
												stroke="currentColor"
												class="w-4 h-4"
											>
												<path
													stroke-linecap="round"
													stroke-linejoin="round"
													d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0"
												/>
											</svg>
										</button>
									</Tooltip>
								{/if}
							</div>
						</td>
					</tr>
				{/each}
			</tbody>
		</table>
	</div>

	<div class=" text-gray-500 text-xs mt-1.5 text-right">
		ⓘ {$i18n.t("Click on the user role button to change a user's role.")}
	</div>

	<Pagination bind:page count={users.length} />
{/if}

<style>
	.font-mona {
		font-family: 'Mona Sans';
	}

	.scrollbar-hidden::-webkit-scrollbar {
		display: none; /* for Chrome, Safari and Opera */
	}

	.scrollbar-hidden {
		-ms-overflow-style: none; /* IE and Edge */
		scrollbar-width: none; /* Firefox */
	}
</style>
