INSTALL_DIR=/opt/hiveos-prometheus
SYSTEMD_SVC_DIR=/etc/systemd/system
SYSTEMD_RELOAD=/bin/systemctl daemon-reload
SERVICE_NAME=hiveos-exporter.service

install:
	install -d ${INSTALL_DIR}/bin
	install -g root -o root -m 755 src/hiveos-exporter.py ${INSTALL_DIR}/bin/
	install -g root -o root -m 644 systemd/${SERVICE_NAME} ${SYSTEMD_SVC_DIR}/
	${SYSTEMD_RELOAD}

uninstall:
	systemctl disable ${SERVICE_NAME} --now
	rm -rf ${INSTALL_DIR}
	rm -f ${SYSTEMD_SVC_DIR}/${SERVICE_NAME}
	${SYSTEMD_RELOAD}