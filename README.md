# DOER 2.0
DOER is an initiative to provide access of educational resources to students of remote villages that don't have internet connection.
#####  *This software is constantly under development and some breaking changes might happen in future.* 
 

## About

DOER 2.0 is a pool of many open-source educational resources which could be accessed offline by the students. Following is the brief account of these open-source resources.
1. NROER (National Repository of Open Educational Resources)
2. Phet
3. Turtle
4. Snap and Edgy
5. Sugarizer
6. Kolibri
7. Music Blocks
8. Wikipedia
9. Wordpress with H5P 

## ISO File Creation
For installing a fresh instance of DOER, we have built an ISO image, which could simply be copied and booted anywhere (along with other post-installation scripts) for creating another instance. Using ISO is a far more better way than cloning the complete DOER onto another hard disk. A major problem associated with cloning is our inability to use the leftover space for other purposes. We have used an open-source tool called simple-cdd for building an ISO image which will install debian9 and freedom-box package. Booting the ISO file would install debian9 as a base OS and then freedom-box as a debian package. Also the installation takes place completely offline which is also an achievement of our project.

## Self Replication Feature

The previous version of DOER used the Linux command “dd” short for “disk dump” to achieve self replication. This meant that a school representative had to carry the internal hard-drive physically and manually initiate the cloning procedure. This has 2 major drawbacks: Firstly the disk size should be exactly same as the parent DOER. Any discrepancy in the size of the disk may lead to errors. Secondly, the internal disk of the parent needed to be removed and set-into a cloning device. This means that the parent DOER remained in-operational throughout the process. We overcame both of these limitations by writing a post-installation script. The post installation script can replicate the DOER-applications onto any file-system/storage device. This means that the size of the new machine can be flexible. Also it allows for replication of applications as per requirement. This means that only a part of DOER may also be replicated instead of all the applications. The entire application is written in GUI framework Gtk. This means that the process is user-friendly and can also be performed by a computer-novice.

## Post Installation Scripts

Complimentary GUI wizard to the self-replication script has been written. The post-installation wizard helps install and setup any package that were acquired from a different machine. It calculates space requirements for the new application and sets-it up automatically. It also sets-up reverse-proxy and any additional services required by the package

## Integration and Launching

Master DOER machines would be setup. All DOER peers will attempt to stay in sync with these master machines. This would allow the DOER machines which are connected to the network to maintain and distribute the updated versions of the educational material. Syncthing will carry out the p2p syncing of the DOER peers. NROER repository will be kept in sync using a systemd service on each peer. This service will continously monitor the synced directory for changes. In case of modification, it checks the timestamp and accordingly adds only the changed topics to the local version of the national repository. All this is done in a secure manner using asymmetric encryption so that no one can maliciously exploit the feature.

## Instructions
1. Install simple-cdd 
`apt-get install simple-cdd` 
2. To build an ISO image containing Debian , Freedom Box and other packages `./build_iso.sh` 
3. ISO image path
`./simple-cdd/images/` 
4.  For making USB bootable with this ISO image
`
sudo dd bs=4M if=./simple-cdd/images/debian-9.9-amd64-CD-1.iso of=/dev/sd<?> conv=fdatasync  status=progress`
where `/dev/sd<?>` is the USB device you're writing to (run `lsblk` to see all drives to find out what `<?>` is for your USB)
5. Boot your Machine on which you want to run DOER using above USB device.