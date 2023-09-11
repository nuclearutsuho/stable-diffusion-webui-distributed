import os
import subprocess
from pathlib import Path
import gradio
from .shared import logger, log_level
from .Worker import Worker, State
from modules.shared import state as webui_state
from typing import List
from threading import Thread

worker_select_dropdown = None


class UI:
    """extension user interface related things"""

    def __init__(self, script, world):
        self.script = script
        self.world = world

    # handlers
    @staticmethod
    def user_script_btn():
        """executes a script placed by the user at <extension>/user/sync*"""
        user_scripts = Path(os.path.abspath(__file__)).parent.parent.joinpath('user')

        for file in user_scripts.iterdir():
            logger.debug(f"found possible script {file.name}")
            if file.is_file() and file.name.startswith('sync'):
                user_script = file

        suffix = user_script.suffix[1:]

        if suffix == 'ps1':
            subprocess.call(['powershell', user_script])
            return True
        else:
            f = open(user_script, 'r')
            first_line = f.readline().strip()
            if first_line.startswith('#!'):
                shebang = first_line[2:]
                subprocess.call([shebang, user_script])
                return True

        return False

    def benchmark_btn(self):
        """benchmarks all registered workers that aren't unavailable"""
        logger.info("Redoing benchmarks...")
        self.world.benchmark(rebenchmark=True)

    @staticmethod
    def clear_queue_btn():
        """debug utility that will clear the internal webui queue. sometimes good for jams"""
        logger.debug(webui_state.__dict__)
        webui_state.end()

    def status_btn(self):
        """updates a simplified overview of registered workers and their jobs"""
        worker_status = ''
        workers = self.world._workers

        for worker in workers:
            if worker.master:
                continue

            worker_status += f"{worker.label} at {worker.address} is {worker.state.name}\n"

        # TODO replace this with a single check to a state flag that we should make in the world class
        for worker in workers:
            if worker.state == State.WORKING:
                return self.world.__str__(), worker_status

        return 'No active jobs!', worker_status

    def save_btn(self, thin_client_mode, job_timeout):
        """updates the options visible on the settings tab"""

        self.world.thin_client_mode = thin_client_mode
        logger.debug(f"thin client mode is now {thin_client_mode}")
        job_timeout = int(job_timeout)
        self.world.job_timeout = job_timeout
        logger.debug(f"job timeout is now {job_timeout} seconds")
        self.world.save_config()

    def save_worker_btn(self, label, address, port, tls, disabled):
        """creates or updates the worker selected in the worker config tab"""

        # determine what state to save
        # if updating a pre-existing worker then grab its current state
        state = State.IDLE
        if disabled:
            state = State.DISABLED
        else:
            original = self.world[label]
            if original is not None:
                state = original.state if original.state != State.DISABLED else State.IDLE

        self.world.add_worker(
            label=label,
            address=address,
            port=port,
            tls=tls,
            state=state
        )
        self.world.save_config()

        # visibly update which workers can be selected
        labels = [worker.label for worker in self.selectable_remote_workers()]
        return gradio.Dropdown.update(choices=labels)

    def selectable_remote_workers(self) -> List[Worker]:
        """gets a list of all registered remote workers"""
        remote_workers = []

        for worker in self.world._workers:
            if worker.master:
                continue
            remote_workers.append(worker)
        remote_workers = sorted(remote_workers, key=lambda x: x.label)

        return remote_workers

    def remove_worker_btn(self, worker_label):
        """removes, from disk and memory, whatever worker is selected on the worker config tab"""
        # remove worker from memory
        for worker in self.world._workers:
            if worker.label == worker_label:
                self.world._workers.remove(worker)

        # remove worker from disk
        self.world.save_config()

        # visibly update which workers can be selected
        labels = [x.label for x in self.selectable_remote_workers()]
        return gradio.Dropdown.update(choices=labels)

    def populate_worker_config_from_selection(self, selection):
        """populates the ui components on the worker config tab with the current values of the selected worker"""
        avail_models = None
        selected_worker = self.world[selection]

        avail_models = selected_worker.available_models()
        if avail_models is not None:
            avail_models.append('None')  # for disabling override

        return [
            gradio.Textbox.update(value=selected_worker.address),
            gradio.Textbox.update(value=selected_worker.port),
            gradio.Checkbox.update(value=selected_worker.tls),
            gradio.Dropdown.update(choices=avail_models),
            gradio.Checkbox.update(value=True if selected_worker.state == State.DISABLED else False)
        ]

    def override_worker_model(self, model, worker_label):
        """forces a worker to always use the selected model in future requests"""
        worker = self.world[worker_label]

        if model == "None":
            worker.model_override = None
        else:
            worker.model_override = model

            # set model on remote early
            Thread(target=worker.load_options, args=(model,)).start()

    # end handlers
    def create_ui(self):
        """creates the extension UI within a gradio.Box() and returns it"""
        with gradio.Box() as root:
            with gradio.Accordion(label='Distributed', open=False):
                with gradio.Tab('Status') as status_tab:
                    status = gradio.Textbox(elem_id='status', show_label=False)
                    status.placeholder = 'Refresh!'
                    jobs = gradio.Textbox(elem_id='jobs', label='Jobs', show_label=True)
                    jobs.placeholder = 'Refresh!'

                    refresh_status_btn = gradio.Button(value='Refresh')
                    refresh_status_btn.style(size='sm')
                    refresh_status_btn.click(self.status_btn, inputs=[], outputs=[jobs, status])

                    status_tab.select(fn=self.status_btn, inputs=[], outputs=[jobs, status])

                with gradio.Tab('Utils'):
                    refresh_checkpoints_btn = gradio.Button(value='Refresh checkpoints')
                    refresh_checkpoints_btn.style(full_width=False)
                    refresh_checkpoints_btn.click(self.world.refresh_checkpoints)

                    run_usr_btn = gradio.Button(value='Run user script')
                    run_usr_btn.style(full_width=False)
                    run_usr_btn.click(self.user_script_btn)

                    interrupt_all_btn = gradio.Button(value='Interrupt all', variant='stop')
                    interrupt_all_btn.style(full_width=False)
                    interrupt_all_btn.click(self.world.interrupt_remotes)

                    redo_benchmarks_btn = gradio.Button(value='Redo benchmarks', variant='stop')
                    redo_benchmarks_btn.style(full_width=False)
                    redo_benchmarks_btn.click(self.benchmark_btn, inputs=[], outputs=[])

                    reload_config_btn = gradio.Button(value='Reload config from file')
                    reload_config_btn.style(full_width=False)
                    reload_config_btn.click(self.world.load_config)

                    reconnect_lost_workers_btn = gradio.Button(value='Attempt reconnection with remotes')
                    reconnect_lost_workers_btn.style(full_width=False)
                    reconnect_lost_workers_btn.click(self.world.ping_remotes)

                    if log_level == 'DEBUG':
                        clear_queue_btn = gradio.Button(value='Clear local webui queue', variant='stop')
                        clear_queue_btn.style(full_width=False)
                        clear_queue_btn.click(self.clear_queue_btn)

                with gradio.Tab('Worker Config'):
                    worker_select_dropdown = gradio.Dropdown(
                        [x.label for x in self.selectable_remote_workers()],
                        info='Select a pre-existing worker or enter a label for a new one',
                        label='Label',
                        allow_custom_value=True
                    )
                    worker_address_field = gradio.Textbox(label='Address', placeholder='localhost')
                    worker_port_field = gradio.Textbox(label='Port', placeholder='7860')
                    worker_tls_cbx = gradio.Checkbox(
                        label='connect using https'
                    )
                    worker_disabled_cbx = gradio.Checkbox(
                        label='disabled'
                    )

                    with gradio.Accordion(label='Advanced'):
                        model_override_dropdown = gradio.Dropdown(label='Model override')
                        model_override_dropdown.select(self.override_worker_model,
                                                       inputs=[model_override_dropdown, worker_select_dropdown])

                    with gradio.Row():
                        save_worker_btn = gradio.Button(value='Add/Update Worker')
                        save_worker_btn.click(self.save_worker_btn,
                                              inputs=[worker_select_dropdown,
                                                      worker_address_field,
                                                      worker_port_field,
                                                      worker_tls_cbx,
                                                      worker_disabled_cbx],
                                              outputs=[worker_select_dropdown]
                                              )
                        remove_worker_btn = gradio.Button(value='Remove Worker', variant='stop')
                        remove_worker_btn.click(self.remove_worker_btn, inputs=worker_select_dropdown,
                                                outputs=[worker_select_dropdown])

                    worker_select_dropdown.select(
                        self.populate_worker_config_from_selection,
                        inputs=worker_select_dropdown,
                        outputs=[
                            worker_address_field,
                            worker_port_field,
                            worker_tls_cbx,
                            model_override_dropdown,
                            worker_disabled_cbx
                        ]
                    )

                with gradio.Tab('Settings'):
                    thin_client_cbx = gradio.Checkbox(
                        label='Thin-client mode (experimental)',
                        info="Only generate images using remote workers. There will be no previews when enabled.",
                        value=self.world.thin_client_mode
                    )
                    job_timeout = gradio.Number(
                        label='Job timeout', value=self.world.job_timeout,
                        info="Seconds until a worker is considered too slow to be assigned an"
                             " equal share of the total request. Longer than 2 seconds is recommended."
                    )

                    save_btn = gradio.Button(value='Update')
                    save_btn.click(fn=self.save_btn, inputs=[thin_client_cbx, job_timeout])

                with gradio.Tab('Help'):
                    gradio.Markdown(
                        """
                        - [Discord Server 🤝](https://discord.gg/Jpc8wnftd4)
                        - [Github Repository </>](https://github.com/papuSpartan/stable-diffusion-webui-distributed)
                        """
                    )

            return root, [thin_client_cbx, job_timeout]
