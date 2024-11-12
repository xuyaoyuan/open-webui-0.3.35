<script>
    import { getContext, tick, onMount } from 'svelte';
    import Tooltip from '$lib/components/common/Tooltip.svelte';
    import { user } from '$lib/stores';
	import Pagination from '$lib/components/common/Pagination.svelte';
    import { getResponses, DeleteResponseById } from '$lib/apis/responses';
    import GarbageBin from '$lib/components/icons/GarbageBin.svelte';
	import { toast } from 'svelte-sonner';
	import ConfirmDialog from '$lib/components/common/ConfirmDialog.svelte';
    import ChevronDown from '$lib/components/icons/ChevronDown.svelte';
    import ChevronUp from '$lib/components/icons/ChevronUp.svelte';
    const i18n = getContext('i18n');

    let loaded = false;
    let responses = [];
    let page=1;
    let search_username = '';
    let search ='';

    let sortKey = 'question_day'; // default sort key
	let sortOrder = 'asc'; // default sort order
    let showDeleteConfirmDialog = false;
    let tmpResponseId = '';

    function setSortKey(key) {
		if (sortKey === key) {
			sortOrder = sortOrder === 'asc' ? 'desc' : 'asc';
		} else {
			sortKey = key;
			sortOrder = 'asc';
		}
	}

    const deleteResponseHandler = async (id) => {
        const res = await DeleteResponseById(localStorage.token, id).catch((error)=>{
            toast.error(error);
            return null;
        });
        if (res) {
            responses = await getResponses(localStorage.token);
            tmpResponseId = '';
            toast.success($i18n.t('Success Delete Response Record'));
        }
    }

    onMount(async () => {
        const containerElement = document.getElementById('admin-responses-tabs-container');
        responses = await getResponses(localStorage.token);
        loaded = true;
    });
</script>

<ConfirmDialog
    bind:show={showDeleteConfirmDialog}
    on:confirm={() => {
        deleteResponseHandler(tmpResponseId);
    }}
/>


{#if loaded}
    <div class="scrollbar-hidden relative whitespace-nowrap overflow-x-auto max-w-full">
        <input
            class="w-full md:w-60 rounded-xl py-1.5 px-4 text-sm dark:text-gray-300 dark:bg-gray-850 outline-none"
            placeholder={$i18n.t('Search')}
            bind:value={search}
        />
        <table class="w-full text-sm text-left text-gray-500 dark:text-gray-400 table-auto max-w-full">
            <thead class="text-xs text-gray-700 uppercase bg-gray-50 dark:bg-gray-850 dark:text-gray-400">
                <tr>
                    <th
                        scope="col"
                        class="px-3 py-2 cursor-pointer select-none"
                        on:click={() => setSortKey('question_day')}
                    >
                        <div class="flex gap-1.5 items-center">
                            {$i18n.t('FeedbackTime')}

                            {#if sortKey === 'question_day'}
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
                        class="px-3 py-2 cursor-pointer select-none"
                        on:click={() => setSortKey('user_id')}
                    >
                        <div class="flex gap-1.5 items-center">
                            {$i18n.t('UserName')}

                            {#if sortKey === 'user_id'}
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
                        class="px-3 py-2 cursor-pointer select-none"
                        on:click={() => setSortKey('used_model')}
                    >
                        <div class="flex gap-1.5 items-center">
                            {$i18n.t('UseModel')}

                            {#if sortKey === 'used_model'}
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
                        class="px-3 py-2 cursor-pointer select-none"
                        on:click={() => setSortKey('feedback')}
                    >
                        <div class="flex gap-1.5 items-center">
                            {$i18n.t('Feedback')}

                            {#if sortKey === 'feedback'}
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
                        class="px-3 py-2 cursor-pointer select-none"
                        on:click={() => setSortKey('user_question')}
                    >
                        <div class="flex gap-1.5 items-center">
                            {$i18n.t('User Question')}

                            {#if sortKey === 'user_question'}
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
                        class="px-3 py-2 cursor-pointer select-none"
                        on:click={() => setSortKey('model_response')}
                    >
                        <div class="flex gap-1.5 items-center">
                            {$i18n.t('Model Response')}

                            {#if sortKey === 'model_response'}
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
                        class="px-3 py-2 cursor-pointer select-none"
                        on:click={() => setSortKey('user_feedback_content')}
                    >
                        <div class="flex gap-1.5 items-center">
                            {$i18n.t('User Feedback Content')}

                            {#if sortKey === 'user_feedback_content'}
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
                        class="px-3 py-2 cursor-pointer select-none"
                        on:click={() => setSortKey('userselectreason')}
                    >
                        <div class="flex gap-1.5 items-center">
                            {$i18n.t('User Feedback Option')}

                            {#if sortKey === 'userselectreason'}
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
            
            <tbody>
				{#each responses
					.filter((response) => {
						if (search === '') {
							return true;
						} else {
							let name = response.user_id.toLowerCase();
							const query = search.toLowerCase();
							//新增搜尋欄位，使用者的部門也能夠搜尋。
							return name.includes(query) || response.used_model.toLowerCase().includes(query);
						}
					})
					.sort((a, b) => {
						if (a[sortKey] < b[sortKey]) return sortOrder === 'asc' ? -1 : 1;
						if (a[sortKey] > b[sortKey]) return sortOrder === 'asc' ? 1 : -1;
						return 0;
					})
					.slice((page - 1) * 20, page * 20) as response}
                    <tr class="bg-white border-b dark:bg-gray-900 dark:border-gray-850 text-xs">
                        <td class=" px-3 py-2 text-black"style="word-break: break-word;"> {response.question_day} </td>
                        <td class=" px-3 py-2 text-black" style="white-space: pre-wrap; word-break: break-all;"> {response.user_id} </td>
                        <td class=" px-3 py-2 text-black" style="white-space: pre-wrap; word-break: break-all;"> {response.used_model} </td>
                        <td class=" px-3 py-2 text-black" style="white-space: pre-wrap; word-break: break-all;"> 
                            {#if response.feedback === 'Bad'}
                                <span class="text-red-500" style="font-weight: bold;">{response.feedback} </span>
                            {:else}
                                <span class="text-green-500" style="font-weight: bold;">{response.feedback}</span>
                            {/if}
                        </td>
                        <td class=" px-3 py-2 text-black" style="white-space: pre-wrap; word-break: break-all;"> {response.userprompt} </td>
                        <td class=" px-3 py-2 text-black" style="max-width: 500px; white-space: pre-wrap; word-break: break-all;"> {response.model_ans} </td>
                        <td class=" px-3 py-2 text-black" style="white-space: pre-wrap; word-break: break-all;"> {response.usercomment} </td>
                        <td class=" px-3 py-2 text-black" style="white-space: pre-wrap; word-break: break-all;"> {response.userselectreason} </td>
                        <td class="px-3 py-2 text-right">
							<div class="flex justify-end w-full">
                                <Tooltip content={$i18n.t('Delete This Response Record')}>
                                    <button
                                        class="self-center w-fit text-sm px-2 py-2 hover:bg-black/5 dark:hover:bg-white/5 rounded-xl"
                                        on:click={async () =>{
                                            showDeleteConfirmDialog = true;
                                            tmpResponseId = response.response_id;
                                        }}
                                    >
                                    <GarbageBin strokeWidth="2" />
                                    </button>
                                </Tooltip>
                            </div>
                        </td>
                    </tr>
                {/each}
            </tbody>
        </table>
    </div>
    <Pagination bind:page count={responses.length} />
{/if}
