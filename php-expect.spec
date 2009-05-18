%define modname expect
%define soname %{modname}.so
%define inifile A68_%{modname}.ini

Summary:	PHP extension for expect library
Name:		php-%{modname}
Version:	0.2.5
Release:	%mkrel 5
Group:		Development/PHP
License:	PHP License
URL:		http://pecl.php.net/package/expect
Source0:	http://pecl.php.net/get/%{modname}-%{version}.tgz
Requires(pre): rpm-helper
Requires(postun): rpm-helper
Requires(pre):  apache-mod_php
BuildRequires:	php-devel >= 3:5.2.0
BuildRequires:	expect-devel
BuildRequires:	file
BuildRoot:	%{_tmppath}/%{name}-%{version}-buildroot

%description
This extension allows to interact with processes through PTY, using expect
library.

%prep

%setup -q -n %{modname}-%{version}
[ "../package*.xml" != "/" ] && mv ../package*.xml .

# fix permissions
find . -type f | xargs chmod 644

# strip away annoying ^M
find . -type f|xargs file|grep 'CRLF'|cut -d: -f1|xargs perl -p -i -e 's/\r//'
find . -type f|xargs file|grep 'text'|cut -d: -f1|xargs perl -p -i -e 's/\r//'

# lib64 fix
perl -pi -e "s|/lib\b|/%{_lib}|g" config.m4

%build
%serverbuild

phpize
%configure2_5x --with-libdir=%{_lib} \
    --with-%{modname}=shared,%{_prefix}

# borked libname
libexpect=`basename %{_libdir}/libexpect*.so | sed -e 's/^lib//' | sed -e 's/\.so$//'`
perl -pi -e "s|^EXPECT_SHARED_LIBADD.*|EXPECT_SHARED_LIBADD=-l$libexpect|g" Makefile

%make

%install
rm -rf %{buildroot}

install -d %{buildroot}%{_sysconfdir}/logrotate.d
install -d %{buildroot}%{_sysconfdir}/php.d
install -d %{buildroot}%{_libdir}/php/extensions
install -d %{buildroot}/var/log/httpd

install -m0755 modules/%{soname} %{buildroot}%{_libdir}/php/extensions/

cat > %{buildroot}%{_sysconfdir}/php.d/%{inifile} << EOF
extension = %{soname}

[expect]
;expect.logfile = /var/log/httpd/%{name}.log
expect.loguser = On
expect.timeout = 10
EOF

# install log rotation stuff
cat > %{buildroot}%{_sysconfdir}/logrotate.d/%{name} << EOF
/var/log/httpd/%{name}.log {
    create 644 apache apache
    monthly
    compress
    missingok
}
EOF

touch %{buildroot}/var/log/httpd/%{name}.log

%post
if [ $1 = 1 ]; then
    %create_ghostfile /var/log/httpd/%{name}.log apache apache 644
fi

if [ -f /var/lock/subsys/httpd ]; then
    %{_initrddir}/httpd restart >/dev/null || :
fi

%postun
if [ "$1" = "0" ]; then
    if [ -f /var/lock/subsys/httpd ]; then
	%{_initrddir}/httpd restart >/dev/null || :
    fi
fi

%clean
rm -rf %{buildroot}

%files 
%defattr(-,root,root)
%doc package*.xml
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/logrotate.d/%{name}
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/php.d/%{inifile}
%attr(0755,root,root) %{_libdir}/php/extensions/%{soname}
%ghost %attr(0644,apache,apache) /var/log/httpd/%{name}.log
