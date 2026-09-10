include $(TOPDIR)/rules.mk

PKG_NAME:=router-guard
PKG_VERSION:=1.0.0
PKG_RELEASE:=1

include $(INCLUDE_DIR)/package.mk

define Package/router-guard
  SECTION:=net
  CATEGORY:=Network
  TITLE:=ShorlyNot Router Guard
  DEPENDS:=+nftables
endef

define Package/router-guard/description
  Router guard daemon for ShorlyNot project.
endef

define Package/router-guard/conffiles
/etc/config/router_guard
endef

define Build/Compile
endef

define Package/router-guard/install
	$(INSTALL_DIR) $(1)/usr/bin
	$(INSTALL_BIN) ./files/router_guard.sh $(1)/usr/bin/

	$(INSTALL_DIR) $(1)/etc/init.d
	$(INSTALL_BIN) ./files/router_guard.init $(1)/etc/init.d/router_guard

	$(INSTALL_DIR) $(1)/etc/config
	$(INSTALL_CONF) ./files/router_guard.config $(1)/etc/config/router_guard

	$(INSTALL_DIR) $(1)/etc
	$(INSTALL_DATA) ./files/firewall.router_guard $(1)/etc/
endef

define Package/router-guard/postinst
#!/bin/sh
if [ -z "$${IPKG_INSTROOT}" ]; then
	/etc/init.d/router_guard enable
fi
exit 0
endef

$(eval $(call BuildPackage,router-guard))
