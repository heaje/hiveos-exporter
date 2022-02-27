INSTALL_DIR=/opt/hiveos-exporter
SYSTEMD_SVC_DIR=/etc/systemd/system
SYSTEMD_RELOAD=/bin/systemctl daemon-reload
SERVICE_NAME=hiveos-exporter pool-exporter

install:
	install -d -g root -o root -m 755 ${INSTALL_DIR}/bin ${INSTALL_DIR}/etc ${INSTALL_DIR}/pool
	install -g root -o root -m 755 bin/* ${INSTALL_DIR}/bin/
	install -g root -o root -m 640 etc/* ${INSTALL_DIR}/etc/
	install -g root -o root -m 644 pool/* ${INSTALL_DIR}/pool/
	install -g root -o root -m 644 systemd/* ${SYSTEMD_SVC_DIR}/
	${SYSTEMD_RELOAD}

uninstall:
	for service in "${SERVICE_NAME}"; do \
		systemctl disable $$service --now; \
		rm -f ${SYSTEMD_SVC_DIR}/$${service}.service; \
	done
	rm -rf ${INSTALL_DIR}
	${SYSTEMD_RELOAD}