#!/usr/bin/env python
# coding:UTF8
# author : zhaohui mail:zhaohui@meizu.com

import re,socket,threadpool,requests,base64,StringIO

import datetime


def fetch_gfw_domains():
    domains = set()
    custom = open("custom.txt","r")
    response = requests.get("https://raw.githubusercontent.com/racaljk/hosts/master/hosts")
    if response.ok and response.content:
        domain = None
        contents = response.content + "\r\n" + custom.read()
        stream = StringIO.StringIO(contents)
        for domain in stream.readlines():
            domain = domain.strip().split("\t")[1] if domain.strip().find("\t") >= 0 else domain.strip()
            if not domain.startswith("#") and domain:
                matches = re.search(r"([a-zA-Z0-9-_]{1,}\.){1,}[a-zA-Z0-9-_]{1,}",domain,re.U|re.I)
                if matches and not re.match(r"(\d{1,}\.){1,}\d{1,}",domain,re.U|re.I):
                    domains.add(matches.group(0))
    custom.close()
    return domains


def resolve_domain(domain,resolves):
    address = None
    try:
        address = socket.gethostbyname(domain)
        resolves[domain] = address
        print domain + " : " + address + " : " + str(len(resolves.keys()))
    except:
        address = None
    return address


def map_domains():
    resolves = {}
    pool = threadpool.ThreadPool(10)
    domains = fetch_gfw_domains()
    for d in domains:
        worker = threadpool.WorkRequest(callable_=resolve_domain,args=(d,resolves))
        pool.putRequest(worker)
    pool.wait()

    iptables = open("iptables.sh","w")
    dnsmasq = open("dnsmasq.conf","w")

    iptables.write("#!/bin/sh\n")
    iptables.write("# HOST2IPTABLES BY SOL\n")
    iptables.write("# %s\n" % datetime.datetime.now())
    iptables.write("iptables -t nat -N SHADOWSOCKS\n")
    iptables.write("iptables -t nat -A PREROUTING -p tcp -j SHADOWSOCKS\n")

    dnsmasq.write("# HOST2DNSMASQ BY SOL\n")
    dnsmasq.write("# %s\n" % datetime.datetime.now())

    for k in resolves.keys():
        iptables.write("iptables -t nat -A SHADOWSOCKS -d %s -p tcp -j REDIRECT --to-ports 1080\n" % resolves[k])
        dnsmasq.write("address=/%s/%s\n" % (k,resolves[k]))

    iptables.flush()
    dnsmasq.flush()

    iptables.close()
    dnsmasq.close()


if __name__ == "__main__":
    map_domains()
