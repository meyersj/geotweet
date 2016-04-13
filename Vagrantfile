# -*- mode: ruby -*-
# vi: set ft=ruby :


Vagrant.configure(2) do |config|

  # set these environment variables to deploy to digital ocean Droplet
  if ENV['DEPLOY_MODE'] == 'digitalocean'
    config.vm.hostname = ENV['DO_SERVER_NAME']
    config.vm.box = "digital_ocean"
    config.ssh.private_key_path = ENV['DO_SSH_KEY']
    config.vm.provider :digital_ocean do |provider|
      provider.token = ENV['DO_API_TOKEN']
      provider.image = 'ubuntu-14-04-x64'
      provider.region = "SFO1"
      provider.size = "512MB"
      provider.name = "vagrant"
    end
  else
    config.vm.box = "ubuntu/trusty64"
  end    
  
  # Mongo DB
  config.vm.network "forwarded_port", guest: 27017, host: 27017

  config.vm.provider "virtualbox" do |vb|
     vb.gui = false
     vb.memory = "1024"
  end

  # provision machine with pacakges
  config.vm.provision "shell", inline: <<-SHELL
    /vagrant/bin/vagrant_provision.sh
  SHELL

end
