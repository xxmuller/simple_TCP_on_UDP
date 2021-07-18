import socket
import struct
import binascii
import random

while True:
    role = str(input("server/client? [s/c]: "))
    if role == 'c' or role == 's':
        break

while True:
    reports = input("reports? [y/n]: ")
    if reports == 'y' or reports == 'n':
        break

if role == 'c':
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    conn = input("connect? [y/n]: ")
    address = input("address: ")
    port = input("port: ")

    try:
        serverAddressPort = (address, int(port))
        s.sendto(conn.encode("utf-8"), serverAddressPort)

        serverAccept = s.recvfrom(1500)
        accept = int.from_bytes(serverAccept[0], "little")
    except:
        accept = 0

    #hlavicka prveho packetu
    def make_first_header(num_of_packets, fragment_size, checksum):
        header = struct.pack('iiL', num_of_packets, fragment_size, checksum)
        return header


    def make_header(packet_num, check_sum):
        header = struct.pack('iL', packet_num, check_sum)
        return header


    def get_num_of_packets(msg):
        n = 0
        while msg:
            n += 1
            msg = msg[buffer_size:]
        print(f"num of packets ==== {n}")
        return n


    def get_num_of_packets_file(file_path):
        f = open(file_path, "rb")
        file = f.read(buffer_size)

        n = 0
        while file:
            n += 1
            file = f.read(buffer_size)

        print(f"num of packets ==== {n}")
        return n

    #vytvori list packetov pri posielani suboru
    def make_file_list(file_path):
        f = open(file_path, "rb")
        file = f.read(buffer_size)

        packet_list = []
        packet_num = 0

        while file:
            packet_num += 1
            checksum = binascii.crc_hqx(file, 0)

            header = make_header(packet_num, checksum)

            packet = header + file

            packet_list.append(packet)
            file = f.read(buffer_size)

        f.close()
        return packet_list

    #vytvori list packetov pri posielani spravy
    def make_msg_list(client_msg):
        packet_list = []
        packet_num = 0

        while client_msg:
            packet_num += 1
            msg = client_msg
            msg = msg[:buffer_size]
            msg = msg.encode("utf-8")

            client_msg = client_msg[buffer_size:]

            checksum = binascii.crc_hqx(msg, 0)
            header = make_header(packet_num, checksum)

            packet = header + msg

            packet_list.append(packet)
        return packet_list


    def send_msg(msg_from_client):
        num_of_packets = get_num_of_packets(msg_from_client)
        init_msg = "msg".encode("utf-8")
        type_checksum = binascii.crc_hqx(init_msg, 0)

        first_header = make_first_header(num_of_packets, buffer_size, type_checksum)

        while True:
            s.sendto(first_header + init_msg, serverAddressPort)
            confirm = s.recvfrom(1500)[0].decode("utf-8")
            if confirm == "ok":
                print("first packet ok!")
                break
            else:
                s.sendto(first_header + init_msg, serverAddressPort)

        packet_list = make_msg_list(msg_from_client)

        x = 0
        y = 10
        #pocet desiatok packetov
        n = 1
        while True:
            k = 1
            for i in range(x, y):
                if i >= num_of_packets:
                    k = 0
                    break
                s.sendto(packet_list[i], serverAddressPort)

            data = s.recvfrom(1500)[0]
            feedback = data[4:]
            feedback = feedback.decode("utf-8")
            header = data[:4]
            try:
                (failed_pckt,) = struct.unpack("i", header)
            except:
                break
            #ak prisiel chybny packet, tak posle packety od jeho indexu
            if feedback == "fail":
                print(f"packet no. {failed_pckt} failed!")
                for i in range(failed_pckt, y):
                    s.sendto(packet_list[i], serverAddressPort)

            elif feedback == "ok" and reports == 'y':
                print(f"{n}. packets received ok!")

            #ak niektory packet neprisiel, tak znovu posle vsetkych 10 packetov
            elif feedback == '0':
                print("some packets did not come!")
                for i in range(x, y):
                    if i >= num_of_packets:
                        k = 0
                        break
                    s.sendto(packet_list[i], serverAddressPort)

            #ak sa poslali vsetky packety skonci
            if k == 0:
                break
            x += 10
            y += 10
            n += 1

        return 1


    def send_file():
        file_path = input("file path: ")

        #ziskavam typ suboru
        path, file_type = file_path.split('.')
        file_type = file_type.encode("utf-8")

        print(f"file type == {file_type}")

        num_of_packets = get_num_of_packets_file(file_path)
        type_checksum = binascii.crc_hqx(file_type, 0)

        first_header = make_first_header(num_of_packets, buffer_size, type_checksum)

        while True:
            s.sendto(first_header + file_type, serverAddressPort)
            confirm = s.recvfrom(1500)[0].decode("utf-8")
            if confirm == "ok":
                print("first packet ok!")
                break
            else:
                s.sendto(first_header + file_type, serverAddressPort)

        packet_list = make_file_list(file_path)

        #ak chce uzivatel, aby sa poslal chybny packet, tak nastavi nahodne cislo packetu
        if packet_fail == 1:
            fail = random.randint(0, num_of_packets)
        else:
            fail = 0

        x = 0
        y = 10
        #pocet desiatok packetov
        n = 1
        while True:
            k = 1
            for i in range(x, y):
                if i >= num_of_packets:
                    k = 0
                    break
                #ak sa ma poslat chybny packet, tak poslem len hlavicku, bez fragmentu
                if i == fail and packet_fail == 1:
                    print("sending bad packet")
                    s.sendto(packet_list[i][:8], serverAddressPort)
                else:
                    s.sendto(packet_list[i], serverAddressPort)

            data = s.recvfrom(1500)[0]
            feedback = data[4:]
            feedback = feedback.decode("utf-8")
            header = data[:4]
            try:
                (failed_pckt,) = struct.unpack("i", header)
            except:
                break

            #ak je niektory packet chybny, tak posle packety od jeho indexu
            #tak aby ich dokopy bolo 10 aj s tymi pred nim
            if feedback == "fail":
                print(f"packet no. {failed_pckt} failed!")
                for i in range(failed_pckt, y):
                    if i >= num_of_packets:
                        k = 0
                        break
                    s.sendto(packet_list[i], serverAddressPort)

            elif feedback == "ok" and reports == 'y':
                print(f"{n}. packets received ok!")

            #ak nejaky packet neprisiel, tak posle vsetky 10 znovu
            elif feedback == '0':
                print("some packets did not come!")
                for i in range(x, y):
                    if i >= num_of_packets:
                        k = 0
                        break
                    s.sendto(packet_list[i], serverAddressPort)
            if k == 0:
                break
            x += 10
            y += 10
            n += 1

        return 1

    #server sa nastavil na pocuvanie a klient moze posielat
    if accept == 1:
        print("connected...")
        print("send msg = m")
        print("send file = f")
        print("disconnect = d")
        while True:
            while True:
                buffer_size = int(input("size of fragment: "))
                # spravna velkost fragmentu musi byt mensia ako 1460
                # pretoze hlavicka UDP ma 8 bajtov, ip hlavicka ma 20 a moja ma 12 bajtov
                # cize 1500 - 40 = 1460
                if buffer_size >= 1460:
                    print("incorrect buffer size!")
                else:
                    break

            # ma sa poslat chybny packet?
            packet_fail = int(input("failed packet? [1/0]: "))
            user_choice = input("your choice: ")

            s.sendto(user_choice.encode("utf-8"), serverAddressPort)

            if user_choice == 'm':
                msgFromClient = input("your msg: ")
                if send_msg(msgFromClient):
                    print("message sent!")
            elif user_choice == 'f':
                if send_file():
                    print("file sent!")
            elif user_choice == 'd':
                print("disconnected")
                break
    else:
        print("could not connect!")


elif role == 's':
    port = int(input("port: "))
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("", port))

    buffer_size = 1500

    def make_feedback_header(wrong_packet):
        header = struct.pack("i", int(wrong_packet))
        return header


    def receive_msg():
        while True:
            init_data = s.recvfrom(buffer_size)
            packet = init_data[0]
            type_header = packet[:12]
            init_msg = packet[12:]

            (num_of_packets, packet_size, checksum) = struct.unpack("iiL", type_header)
            check = binascii.crc_hqx(init_msg, 0)
            if check == checksum:
                print("first packet ok!")
                s.sendto("ok".encode("utf-8"), address)
                break
            else:
                continue

        msgFromClient = ''

        #vytvorim prazdny list, kde pojdu fragmenty
        frag_list = []
        for i in range(0, num_of_packets):
            frag_list.append("")
        i = 1
        fail = 0
        corr = 0
        time = 3
        failed_pckt = 1
        while True:
            #nastavujem timeout, keby nahodou niektory packet nedojde
            s.settimeout(time)
            try:
                data = s.recvfrom(buffer_size)
                packet = data[0]

                header = packet[:8]
                (packetNum, checkSum) = struct.unpack("iL", header)
                msg = packet[8:]

                check = binascii.crc_hqx(msg, 0)

                msg = msg.decode("utf-8")

                #ak sa checksumy rovnaju packet je ok a da ho do listu
                if check == checkSum:
                    frag_list[packetNum - 1] = msg
                    if fail == 0:
                        corr += 1
                else:
                    print("fail!")
                    if fail == 0:
                        fail = packetNum

                if packetNum == 1 and failed_pckt == 1:
                    fail = 1

                #ak prislo vsetkych 10 packetov ok
                if i % 10 == 0 and corr == 10:
                    header = make_feedback_header(fail)
                    feedback = header + "ok".encode("utf-8")
                    s.sendto(feedback, address)
                    if reports == 'y':
                        print("packet ok!")
                    fail = 0
                    corr = 0
                #ak prislo 10 packetov ale aspon jeden je chybny
                elif i % 10 == 0 and fail != 0:
                    print(f"packet no. {fail} failed!")
                    header = make_feedback_header(fail)
                    feedback = header + "fail".encode("utf-8")
                    s.sendto(feedback, address)
                    i = fail
                    failed_pckt = 0
                    fail = 0
                #ak prisli vsetky
                if packetNum == num_of_packets:
                    s.sendto("ok".encode("utf-8"), address)
                    break
                i += 1
            except:
                #ak nepride 10 packetov do troch sekund vypyta si ich znova
                print("some packets did not come")
                header = make_feedback_header(0)
                feedback = header + "0".encode("utf-8")
                s.sendto(feedback, address)
                i -= 9
                corr = 0
                time = 3

        print("message received!")

        for x in frag_list:
            msgFromClient += x
        print(msgFromClient)


    def receiveFile():
        while True:
            init_data = s.recvfrom(buffer_size)
            packet = init_data[0]
            type_header = packet[:12]
            file_type = packet[12:]

            file_name = "file"
            file_path = file_name + '.' + file_type.decode("utf-8")
            f = open(file_path, 'wb')

            (num_of_packets, packet_size, checksum) = struct.unpack("iiL", type_header)
            check = binascii.crc_hqx(file_type, 0)
            if check == checksum:
                print("first packet ok!")
                s.sendto("ok".encode("utf-8"), address)
                break
            else:
                continue

        # vytvorim prazdny list, kde pojdu fragmenty
        frag_list = []
        for i in range(0, num_of_packets):
            frag_list.append("")

        i = 1
        fail = 0
        corr = 0
        time = 3
        while True:
            # nastavujem timeout, keby nahodou niektory packet nedojde
            s.settimeout(time)
            try:
                data = s.recvfrom(buffer_size)
                packet = data[0]

                header = packet[:8]
                (packetNum, checkSum) = struct.unpack("iL", header)
                file = packet[8:]

                if reports == 'y':
                    print(f"{packetNum} / {num_of_packets} packet = {checkSum}")

                check = binascii.crc_hqx(file, 0)

                # ak sa checksumy rovnaju packet je ok a da ho do listu
                if check == checkSum:
                    frag_list[packetNum - 1] = file
                    if fail == 0:
                        corr += 1
                else:
                    if reports == 'y':
                        print("fail!!!")
                    if fail == 0:
                        fail = packetNum

                if packetNum == 1:
                    fail = 1

                # ak prislo vsetkych 10 packetov ok
                if i % 10 == 0 and corr == 10:
                    header = make_feedback_header(fail)
                    feedback = header + "ok".encode("utf-8")
                    s.sendto(feedback, address)
                    if reports == 'y':
                        print("packet ok!")
                    fail = 0
                    corr = 0

                # ak prislo 10 packetov ale aspon jeden je chybny
                elif i % 10 == 0 and fail != 0:
                    print(f"packet no. {fail} failed!")
                    header = make_feedback_header(fail)
                    feedback = header + "fail".encode("utf-8")
                    s.sendto(feedback, address)
                    i = fail
                    fail = 0

                if packetNum == num_of_packets:
                    s.sendto("ok".encode("utf-8"), address)
                    break
                i += 1
            except:
                # ak nepride 10 packetov do troch sekund vypyta si ich znova
                print("some packets did not come")
                header = make_feedback_header(0)
                feedback = header + "0".encode("utf-8")
                s.sendto(feedback, address)
                i -= 9
                corr = 0
                time = 3

        print("file received!")

        for x in frag_list:
            f.write(x)
        f.close()


    def listen():
        print("listening...")
        while True:
            s.settimeout(40)
            try:
                clientChoice = s.recvfrom(buffer_size)
                choice = clientChoice[0].decode("utf-8")

                if choice == 'm':
                    receive_msg()
                elif choice == 'f':
                    receiveFile()
                elif choice == 'd':
                    print("disconnected...")
                    break
            except:
                print("disconnected...")
                break

    s.settimeout(20)
    try:
        conn = s.recvfrom(buffer_size)
        c = conn[0]
        c = c.decode("utf-8")
        address = conn[1]

        print(c)
        print(address)

        if c == 'y':
            accept = 1
            s.sendto(bytes([accept]), address)
            listen()
    except:
        print("no connection")