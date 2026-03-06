# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
  config.vm.box = "bento/ubuntu-22.04"
  config.vm.hostname = "neo4j-prototype-vm"

  config.vm.network "forwarded_port", guest: 7474, host: 7474, protocol: "tcp", auto_correct: true
  config.vm.network "forwarded_port", guest: 7687, host: 7687, protocol: "tcp", auto_correct: true

  config.vm.synced_folder ".", "/workspace", type: "virtualbox"

  config.vm.provider "virtualbox" do |vb|
    vb.name = "neo4j-prototype-vm"
    vb.cpus = 2
    vb.memory = 4096
  end

  config.vm.provision "shell",
                      path: "scripts/vagrant/provision_neo4j.sh",
                      privileged: true,
                      env: {
                        "NEO4J_PASSWORD" => "password12345",
                        "ALLOW_INSECURE_TLS_BOOTSTRAP" => "true",
                      }
end
