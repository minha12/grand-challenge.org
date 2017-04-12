# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
  config.vm.box = "ubuntu/xenial64"
  config.vm.network "forwarded_port", guest: 8000, host: 8000

  config.vm.provider "virtualbox" do |vb|
    vb.memory = "2048"
  end

  config.vm.provision "shell", inline: <<-SHELL
    apt-get update && apt-get upgrade -y

    apt-get install -y python python-pip python-openssl libpng-dev libfreetype6-dev libxft-dev libmysqlclient-dev libffi-dev 
    
    pip install --upgrade pip
    pip install -r /vagrant/requirements.txt

    wget https://github.com/mozilla/geckodriver/releases/download/v0.15.0/geckodriver-v0.15.0-linux64.tar.gz
    tar -xvzf geckodriver*
    chmod +x geckodriver
    cp geckodriver* /usr/local/bin
  SHELL
end
