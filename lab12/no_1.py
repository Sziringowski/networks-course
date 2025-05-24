import json
import random
from collections import defaultdict
import threading
import queue
import time


class Router:
    def __init__(self, ip):
        self.ip = ip
        self.neighbors = {}
        self.routing_table = {}

    def initialize_routing_table(self):
        self.routing_table = {self.ip: (self.ip, 0)}
        for neighbor, metric in self.neighbors.items():
            self.routing_table[neighbor] = (neighbor, metric)

    def update_routing_table(self, sender_ip, received_table):
        updated = False
        if sender_ip not in self.neighbors:
            return updated
        sender_metric = self.neighbors[sender_ip]
        for dest, (_, received_metric) in received_table.items():
            if dest == self.ip:
                continue
            new_metric = received_metric + sender_metric
            if new_metric > 15:
                continue
            current_entry = self.routing_table.get(dest, (None, float('inf')))
            if new_metric < current_entry[1]:
                self.routing_table[dest] = (sender_ip, new_metric)
                updated = True
        return updated


class Network:
    def __init__(self, routers):
        self.routers = {router.ip: router for router in routers}

    def simulate_step(self):
        messages = []
        for router in self.routers.values():
            for neighbor in router.neighbors:
                messages.append(
                    (neighbor, router.ip, router.routing_table.copy()))
        updates = defaultdict(list)
        for neighbor, sender, table in messages:
            updates[neighbor].append((sender, table))
        any_updated = False
        for neighbor_ip in updates:
            router = self.routers.get(neighbor_ip)
            if not router:
                continue
            for sender_ip, table in updates[neighbor_ip]:
                if sender_ip not in router.neighbors:
                    continue
                if router.update_routing_table(sender_ip, table):
                    any_updated = True
        return any_updated

    def simulate_until_stable(self, verbose=False):
        step = 0
        while True:
            step += 1
            any_updated = self.simulate_step()
            if verbose:
                print(f"--- Simulation step {step} ---")
                for router in self.routers.values():
                    print(f"Router {router.ip} routing table:")
                    self.print_routing_table(router)
                    print()
            if not any_updated:
                break
        print("Simulation stabilized.")

    @staticmethod
    def print_routing_table(router):
        header = "{:<16} {:<16} {:<16} {:<8}".format(
            "[Source IP]", "[Destination IP]", "[Next Hop]", "[Metric]")
        print(header)
        for dest in sorted(router.routing_table):
            next_hop, metric = router.routing_table[dest]
            print("{:<16} {:<16} {:<16} {:<8}".format(
                router.ip, dest, next_hop, metric))


def load_network_from_json(filename):
    with open(filename) as f:
        config = json.load(f)
    routers = []
    for r in config['routers']:
        router = Router(r['ip'])
        router.neighbors = {n['ip']: n['metric'] for n in r['neighbors']}
        router.initialize_routing_table()
        routers.append(router)
    return Network(routers)


if __name__ == "__main__":
    # Прото конфиг
    config = {
        "routers": [
            {
                "ip": "198.71.243.61",
                "neighbors": [{"ip": "42.162.54.248", "metric": 1}]
            },
            {
                "ip": "42.162.54.248",
                "neighbors": [
                    {"ip": "198.71.243.61", "metric": 1},
                    {"ip": "157.105.66.180", "metric": 1}
                ]
            },
            {
                "ip": "157.105.66.180",
                "neighbors": [
                    {"ip": "42.162.54.248", "metric": 1},
                    {"ip": "229.28.61.15", "metric": 1}
                ]
            },
            {
                "ip": "229.28.61.15",
                "neighbors": [{"ip": "157.105.66.180", "metric": 1}]
            }
        ]
    }
    with open('network.json', 'w') as f:
        json.dump(config, f)
    network = load_network_from_json('network.json')
    network.simulate_until_stable(verbose=True)
    print("\nFinal Routing Tables:")
    for router in network.routers.values():
        print(f"Final state of router {router.ip} table:")
        Network.print_routing_table(router)
        print()
