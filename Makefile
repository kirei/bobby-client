SOURCE=		bobby_client

PYTHON=		python3
VENV=		venv
GREEN=		$(VENV)/bin/green -vv

BAD_CERT=	badcert.pem

all:

$(VENV): $(VENV)/.depend

$(VENV)/.depend: requirements.txt
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install -r requirements.txt
	touch $(VENV)/.depend

upgrade-venv::
	$(VENV)/bin/pip install -r requirements.txt --upgrade
	touch $(VENV)/.depend

$(BAD_CERT):
	openssl req -new -x509 -sha256 -days 1000 \
		-newkey rsa:2048 -nodes -keyout $@ \
		-subj "/CN=badcert" -out $@

test: $(BAD_CERT)
	$(GREEN)

test-authentication: $(BAD_CERT)
	$(GREEN) $(SOURCE)/test_authentication*.py

test-device:
	$(GREEN) $(SOURCE)/test_device*.py

test-product:
	$(GREEN) $(SOURCE)/test_product*.py

test-ticket:
	$(GREEN) $(SOURCE)/test_ticket*.py

test-validation:
	$(GREEN) $(SOURCE)/test_validation*.py

test-inspection:
	$(GREEN) $(SOURCE)/test_inspection*.py

test-lifecycle:
	$(GREEN) $(SOURCE)/test_lifecycle*.py

lint: $(VENV)
	$(VENV)/bin/pylama $(SOURCE)

typecheck: $(VENV)
	$(VENV)/bin/mypy $(SOURCE)

clean:
	rm -f $(BAD_CERT)

realclean:
	rm -fr $(VENV)
