
nmcli d wifi connect "Phong Tro Ribo" password 09051141178

ssh root@192.168.1.16
orangepi

sudo dd if=/dev/zero of=/usb.img bs=1M count=512 status=progress conv=fsync
sudo mkdosfs /usb.img -F 32 -I

sudo modprobe g_mass_storage file=/data/usb_partition.img stall=0 removable=1


losetup /dev/loop0 /usb.img
mount /dev/loop0 /mnt/usb/

