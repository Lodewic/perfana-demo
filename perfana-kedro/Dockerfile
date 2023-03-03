FROM jupyter/scipy-notebook:python-3.10.9 as base

USER root
RUN sudo apt-get update && sudo apt-get install libmariadb3 libmariadb-dev openssh-server supervisor -y
RUN pip install mariadb pymongo

USER ${NB_UID}

# install project requirements
COPY src/requirements.txt /home/jovyan/work/src/requirements.txt
RUN pip install -r /home/jovyan/work/src/requirements.txt

# copy entire directory and install our python package editable
COPY . /home/jovyan/work/
RUN pip install -e /home/jovyan/work/src/[dev]

# for jupyter lab
EXPOSE 8888
# for kedro-viz
EXPOSE 4141

CMD ["start.sh", "jupyter",  "lab", "--NotebookApp.token=''"]

# dev target also runs an ssh server to connect IDE for debugging
FROM base as dev

USER root

# Allow root user with password login (Optional)
# RUN sudo sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config

# SSH login fix. Otherwise user is kicked off after login
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd

COPY supervisord.conf /etc/supervisord.conf
RUN echo "jovyan:pwd" | sudo chpasswd
RUN mkdir /var/run/sshd

# for ssh
EXPOSE 22

# RUN ssh server and jupyter lab
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisord.conf"]
