import queue
import threading


## wrapper class for a queue of packets
class Interface:
    ## @param maxsize - the maximum size of the queue storing packets
    def __init__(self, maxsize=0):
        self.in_queue = queue.Queue(maxsize)
        self.out_queue = queue.Queue(maxsize)
    
    ##get packet from the queue interface
    # @param in_or_out - use 'in' or 'out' interface
    def get(self, in_or_out):
        try:
            if in_or_out == 'in':
                pkt_S = self.in_queue.get(False)
                # if pkt_S is not None:
                #     print('getting packet from the IN queue')
                return pkt_S
            else:
                pkt_S = self.out_queue.get(False)
                # if pkt_S is not None:
                #     print('getting packet from the OUT queue')
                return pkt_S
        except queue.Empty:
            return None
        
    ##put the packet into the interface queue
    # @param pkt - Packet to be inserted into the queue
    # @param in_or_out - use 'in' or 'out' interface
    # @param block - if True, block until room in queue, if False may throw queue.Full exception
    def put(self, pkt, in_or_out, block=False):
        if in_or_out == 'out':
            # print('putting packet in the OUT queue')
            self.out_queue.put(pkt, block)
        else:
            # print('putting packet in the IN queue')
            self.in_queue.put(pkt, block)
            
        
## Implements a network layer packet.
class NetworkPacket:
    ## packet encoding lengths 
    dst_S_length = 5
    prot_S_length = 1
    
    ##@param dst: address of the destination host
    # @param data_S: packet payload
    # @param prot_S: upper layer protocol for the packet (data, or control)
    def __init__(self, dst, prot_S, data_S):
        self.dst = dst
        self.data_S = data_S
        self.prot_S = prot_S
        
    ## called when printing the object
    def __str__(self):
        return self.to_byte_S()
        
    ## convert packet to a byte string for transmission over links
    def to_byte_S(self):
        byte_S = str(self.dst).zfill(self.dst_S_length)
        if self.prot_S == 'data':
            byte_S += '1'
        elif self.prot_S == 'control':
            byte_S += '2'
        else:
            raise('%s: unknown prot_S option: %s' %(self, self.prot_S))
        byte_S += self.data_S
        return byte_S
    
    ## extract a packet object from a byte string
    # @param byte_S: byte string representation of the packet
    @classmethod
    def from_byte_S(self, byte_S):
        dst = byte_S[0 : NetworkPacket.dst_S_length].strip('0')
        prot_S = byte_S[NetworkPacket.dst_S_length : NetworkPacket.dst_S_length + NetworkPacket.prot_S_length]
        if prot_S == '1':
            prot_S = 'data'
        elif prot_S == '2':
            prot_S = 'control'
        else:
            raise('%s: unknown prot_S field: %s' %(self, prot_S))
        data_S = byte_S[NetworkPacket.dst_S_length + NetworkPacket.prot_S_length : ]        
        return self(dst, prot_S, data_S)
    

    

## Implements a network host for receiving and transmitting data
class Host:
    
    ##@param addr: address of this node represented as an integer
    def __init__(self, addr):
        self.addr = addr
        self.intf_L = [Interface()]
        self.stop = False #for thread termination
    
    ## called when printing the object
    def __str__(self):
        return self.addr
       
    ## create a packet and enqueue for transmission
    # @param dst: destination address for the packet
    # @param data_S: data being transmitted to the network layer
    def udt_send(self, dst, data_S):
        p = NetworkPacket(dst, 'data', data_S)
        print('%s: sending packet "%s"' % (self, p))
        self.intf_L[0].put(p.to_byte_S(), 'out') #send packets always enqueued successfully
        
    ## receive packet from the network layer
    def udt_receive(self):
        pkt_S = self.intf_L[0].get('in')
        if pkt_S is not None:
            print('%s: received packet "%s"' % (self, pkt_S))
       
    ## thread target for the host to keep receiving data
    def run(self):
        print (threading.currentThread().getName() + ': Starting')
        while True:
            #receive data arriving to the in interface
            self.udt_receive()
            #terminate
            if(self.stop):
                print (threading.currentThread().getName() + ': Ending')
                return
        


## Implements a multi-interface router
class Router:
    
    ##@param name: friendly router name for debugging
    # @param cost_D: cost table to neighbors {neighbor: {interface: cost}}
    # @param max_queue_size: max queue length (passed to Interface)
    def __init__(self, name, cost_D, max_queue_size):
        self.stop = False #for thread termination
        self.name = name
        self.flag = True
        self.interfaces = {}
        #create a list of interfaces
        self.intf_L = [Interface(max_queue_size) for _ in range(len(cost_D))]
        #save neighbors and interfeces on which we connect to them
        self.cost_D = cost_D    # {neighbor: {interface: cost}}
        #TODO: set up the routing table for connected hosts
        self.rt_tbl_D = {name:{name: 0}}
        for router in list(cost_D):
            for interface in list(self.cost_D[router]):
                cost = cost_D[router][interface]
                self.interfaces.update({interface:cost})
                self.rt_tbl_D.update({router : {self.name:cost}})
                
        # {destination: {router: cost}}
        print('%s: Initialized routing table' % self)
        self.print_routes()
    
        
    ## Print routing table
    def print_routes(self):
        #TODO: print the routes as a two dimensional table
        #print("Installing XXX...      ", end="", flush=True)
        print("╒══════", end="", flush=True)
        for each_connection in self.rt_tbl_D:
            print("╤══════", end="", flush=True)
        print("╕")
        
        print("│ " + self.name + "   |", end="", flush=True)
        for each_connection in self.rt_tbl_D:
            print(" " + each_connection + "   |", end="", flush=True)
        print()

        print("╞══════", end="", flush=True)
        for each_connection in self.rt_tbl_D:
            print("╪══════", end="", flush=True)
        print("╡")

        

        print("│ " + self.name + "   |", end="", flush=True)
        for neighbor in self.rt_tbl_D:
            for interface in self.rt_tbl_D[neighbor]:
                print(" " + str(self.rt_tbl_D[neighbor][interface]) + "    |", end="", flush=True)
        print()

        print("╘══════", end="", flush=True)
        for each_connection in self.rt_tbl_D:
            print("╧══════", end="", flush=True)
        print("╛")


    ## called when printing the object
    def __str__(self):
        return self.name


    ## look through the content of incoming interfaces and 
    # process data and control packets
    def process_queues(self):
        for i in range(len(self.intf_L)):
            pkt_S = None
            #get packet from interface i
            pkt_S = self.intf_L[i].get('in')
            #if packet exists make a forwarding decision
            if pkt_S is not None:
                p = NetworkPacket.from_byte_S(pkt_S) #parse a packet out
                if p.prot_S == 'data':
                    self.forward_packet(p,i)
                elif p.prot_S == 'control':
                    self.update_routes(p, i)
                else:
                    raise Exception('%s: Unknown packet type in packet %s' % (self, p))
            

    ## forward the packet according to the routing table
    #  @param p Packet to forward
    #  @param i Incoming interface number for packet p
    def forward_packet(self, p, i):
        try:
            # TODO: Here you will need to implement a lookup into the 
            # forwarding table to find the appropriate outgoing interface
            # for now we assume the outgoing interface is 1
            self.intf_L[1].put(p.to_byte_S(), 'out', True)
            print('%s: forwarding packet "%s" from interface %d to %d' % \
                (self, p, i, 1))
        except queue.Full:
            print('%s: packet "%s" lost on interface %d' % (self, p, i))
            pass


    ## send out route update
    # @param i Interface number on which to send out a routing update
    def send_routes(self, i):
        # TODO: Send out a routing table update
        #create a routing table update packet
        msg = ""
        for neighbor in self.rt_tbl_D:
            if(neighbor == self.name):
                continue
            msg += neighbor
            for router_name in self.rt_tbl_D[neighbor]:
                msg += str(router_name) + str(self.rt_tbl_D[neighbor][router_name])
            msg += "|"
        p = NetworkPacket(0, 'control', msg)
        try:
            print('%s: sending routing update "%s" from interface %d' % (self, p, i))
            self.intf_L[i].put(p.to_byte_S(), 'out', True)
        except queue.Full:
            print('%s: packet "%s" lost on interface %d' % (self, p, i))
            pass


    ## forward the packet according to the routing table
    #  @param p Packet containing routing information
    def update_routes(self, p, i):
        #TODO: add logic to update the routing tables and
        # possibly send out routing updates
        temp_dict = {}
        temp_dict2 = {}
        msg = p.to_byte_S()
        i = 0
        while(i < len(msg)):
            if(msg[i] == "|"):
                cur_router = msg[i-3:i-1]
                cost = int(msg[i-1])
                temp_dict2[cur_router] = cost
                temp_dict[msg[i-5:i-3]] = temp_dict2
            temp_dict2 = {}
            i += 1

        
        for n2 in temp_dict:
            if n2 in self.rt_tbl_D:
                #for (int1), (int2) in zip(self.rt_tbl_D[n1], temp_dict[n2]):
                break
            else:
                temp = 1
                #cur = temp_dict[n2]
                #for router in self.rt_tbl_D:
                #    print(router, cur)
                #    if router == cur:
                #        temp = self.rt_tbl_D[router][self.name]

                #print("TEMP: " + str(temp))
                for cur in temp_dict[n2]:
                    temp += temp_dict[n2][cur]

                temp_dct = {self.name : temp}
                self.rt_tbl_D[n2] = temp_dct
                
        
        print('%s: Received routing update %s from interface %d' % (self, p, i))
        if self.flag:
            for interface in self.interfaces:
                self.send_routes(interface)
            self.flag = False

                
    ## thread target for the host to keep forwarding data
    def run(self):
        print (threading.currentThread().getName() + ': Starting')
        while True:
            self.process_queues()
            if self.stop:
                print (threading.currentThread().getName() + ': Ending')
                return 
