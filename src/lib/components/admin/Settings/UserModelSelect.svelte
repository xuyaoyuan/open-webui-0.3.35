<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { createEventDispatcher } from 'svelte';
	import { onMount, getContext } from 'svelte';

	import Modal from '../../common/Modal.svelte';
	import { WEBUI_BASE_URL } from '$lib/constants';

	const i18n = getContext('i18n');
	const dispatch = createEventDispatcher();

	export let show = false;
    export let user;
    export let TotalModel;
    export let SaveSelectModel;
    let enable_model;
    let SelectModelIndex = [];

	let loading = false;
	let tab = '';
	let inputFiles;

	$: if (show) {
        //初始化SelectModelIndex的數值。
        SelectModelIndex = [];
        // console.log(user); 
        //初始化enable_model的數值。
        enable_model = user.model_selector;
        // console.log(enable_model);
        let tmpString = '';

        for (const element of TotalModel){
            //初始化每個selectd狀態。
            element.selected = false;
            if (enable_model.includes(element.model_id) || enable_model.includes('all model')) {
                element.selected = true;
                tmpString = tmpString + element.model_id + ",";
                SelectModelIndex.push(element.index);
            }
        }
        // console.log(tmpString);
        if (user.model_selector.includes('all model')){

        }else{
            user.model_selector = tmpString;
        }
        // console.log(SelectModelIndex);
	}
    $: if (show === false){
        for (const element of TotalModel){
            element.selected = false;
        };
    }
	
    function toggleSelection(model) {
        if (SelectModelIndex.includes(model.index)) {
            if (user.model_selector.includes('all model')){
                let tmpString = '';
                for (const element of TotalModel){
                    //初始化每個selectd狀態。
                    element.selected = false;
                    if (enable_model.includes(element.model_id) || enable_model.includes('all model')) {
                        element.selected = true;
                        tmpString = tmpString + element.model_id + ",";
                        SelectModelIndex.push(element.index);
                    }
                }
                user.model_selector = tmpString;
            }
            SelectModelIndex.splice(SelectModelIndex.indexOf(model.index), 1);
            TotalModel[model.index].selected = !model.selected;
            user.model_selector = removeFromSelector(user.model_selector,  model.model_id);
            // console.log("removed: "+user.model_selector);
        } else {
            SelectModelIndex.push(model.index);
            TotalModel[model.index].selected = !model.selected;
            user.model_selector = addFromSelector(user.model_selector, model.model_id);
        }
        // console.log(SelectModelIndex);
    }
    function removeFromSelector(selector, id) {
        // console.log("removeing");
        let tmp = selector.split(',');
        // console.log(tmp);
        return selector.split(',').filter(item => item !== id).join(',');
    }
    function addFromSelector (selector, id){
        // console.log("adding");
        let arr = selector ? selector.split(',') : [];
        arr.push(id);
        return arr.join(',');
    }
    //全選動作
    function SelectAllModel (){
        user.model_selector = 'all model';
        SaveSelectModel(user.id, user.model_selector);
    }
    //全部取消選取
    function CancelSelectModel (){
        user.model_selector = ' ';
        SaveSelectModel(user.id, user.model_selector);
    }
</script>


<Modal size="sm" bind:show>
    <div class="flex flex-col">
        <div class=" flex justify-between dark:text-gray-300 px-5 pt-4 pb-2">
			<div class=" text-lg font-medium self-center">{$i18n.t('User Info')}</div>
			<button
				class="self-center"
				on:click={() => {
					show = false;
				}}
			>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					viewBox="0 0 20 20"
					fill="currentColor"
					class="w-5 h-5"
				>
					<path
						d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z"
					/>
				</svg>
			</button>
		</div>
        <table class="flex flex-col w-full md:w-auto">
            <tr class="text-center ml-3 mr-3 border border-gray-500 bg-blue-200">
                {$i18n.t('User Name')}{' : '}{user.name}
            </tr>
            <tr class="flex justify-between items-center ml-5">
                {$i18n.t('Can Use Model')}{' :'}
                <td>
                    <button class="mr-1 mb-3 px-1 py-1 hover:bg-blue-400 bg-gray-300 border border-gray-700"
                    on:click={() => SelectAllModel()}>
                        {$i18n.t("Select All Model")}
                    </button>
                    <button class="mr-3 mb-3 px-1 py-1 hover:bg-blue-400 bg-gray-300 border border-gray-700"
                    on:click={() => CancelSelectModel()}>
                        {$i18n.t("All Model Cancel Select")}
                    </button>
                </td>
                
            </tr>
            <tr>
                <td class="mt-4"> <!-- 添加一些顶部间距 -->
                    {#each TotalModel as model, index}
                        <div class="flex items-center ml-5 mt-3 mb-3">
                            <input type="checkbox" id={'${model.model_id}'} class="form-checkbox h-5 w-5 text-blue-600"
                            bind:checked={model.selected} on:change={() => toggleSelection(model)}/>
                            <label for={'${index}'} class="ml-2">{model.model_id}</label>
                        </div>
                    {/each}
                </td>
            </tr>
        </table>
        <div class="flex justify-end mt-auto">
            <button class="mr-5 mb-3 px-1 py-1 hover:bg-blue-400 bg-gray-300 border border-gray-700"
            on:click={() => SaveSelectModel(user.id, user.model_selector)}>
                {$i18n.t("Done")}
            </button>
        </div>
    </div>
</Modal>