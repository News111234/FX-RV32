flowchart TB
    subgraph SOC [SoC 顶层]
        subgraph CORE [处理器核心 Core]
            direction TB
            IFU[取指单元 IFU]:::if
            IDU[译码单元 IDU]:::id
            EXU[执行单元 EXU]:::ex
            MEM[访存单元 MEM]:::mem
            WBU[写回单元 WBU]:::wb
            PIPELINE[流水线寄存器]:::pipeline
            HAZARD[冒险与转发]:::ctrl
            CSR[CSR与中断]:::csr

            IFU --> PIPELINE --> IDU --> PIPELINE --> EXU --> PIPELINE --> MEM --> PIPELINE --> WBU
            HAZARD -->|stall/flush| PIPELINE
            HAZARD -->|前递| EXU
            CSR -->|中断| IFU
        end

        subgraph BUS_PERIPH [总线与外设]
            direction LR
            BUS[总线仲裁器<br/>bus_arbiter]:::bus
            RAM[数据 RAM<br/>data_ram]:::ram
            UART[UART]:::periph
            GPIO[GPIO]:::periph
            TIMER[定时器]:::periph
            SPI[SPI]:::periph
            I2C[I2C]:::periph

            BUS --- RAM
            BUS --- UART
            BUS --- GPIO
            BUS --- TIMER
            BUS --- SPI
            BUS --- I2C
        end

        subgraph INSTR_ROM [指令存储器]
            ROM[指令 ROM<br/>inst_rom]:::rom
        end

        CORE -->|取指地址| ROM
        ROM -->|指令| CORE

        CORE -->|读写请求+地址+写数据| BUS
        BUS -->|读数据| CORE

        BUS -->|写数据| RAM
        RAM -->|读数据| BUS
        BUS -->|写数据| UART
        UART -->|读数据| BUS
        BUS -->|写数据| GPIO
        GPIO -->|读数据| BUS
        BUS -->|写数据| TIMER
        TIMER -->|读数据| BUS
        BUS -->|写数据| SPI
        SPI -->|读数据| BUS
        BUS -->|写数据| I2C
        I2C -->|读数据| BUS

        UART -->|中断| CORE
        GPIO -->|中断| CORE
        TIMER -->|中断| CORE
        SPI -->|中断| CORE
        I2C -->|中断| CORE
    end

    classDef if fill:#D6EAF8,stroke:#1F618D,stroke-width:2px,color:#1A5276
    classDef id fill:#D5F5E3,stroke:#1E8449,stroke-width:2px,color:#1E6F3F
    classDef ex fill:#FCF3CF,stroke:#B7950B,stroke-width:2px,color:#7D6608
    classDef mem fill:#E8DAEF,stroke:#7D3C98,stroke-width:2px,color:#6C3483
    classDef wb fill:#FAD7A0,stroke:#CA6F1E,stroke-width:2px,color:#935116
    classDef pipeline fill:#EAFAF1,stroke:#1E8449,stroke-width:1px,color:#1E6F3F
    classDef ctrl fill:#F9E79F,stroke:#7D6608,stroke-width:2px,color:#7D6608
    classDef csr fill:#D7BDE2,stroke:#6C3483,stroke-width:2px,color:#6C3483
    classDef bus fill:#A9CCE3,stroke:#1B4F72,stroke-width:2px,color:#1B4F72
    classDef ram fill:#D6EAF8,stroke:#1F618D,stroke-width:2px,color:#1A5276
    classDef periph fill:#F5B7B1,stroke:#C0392B,stroke-width:2px,color:#C0392B
    classDef rom fill:#FCF3CF,stroke:#B7950B,stroke-width:2px,color:#7D6608

    style SOC fill:#F8F9F9,stroke:#AAB7B8,stroke-width:1px
    style CORE fill:#F4F6F7,stroke:#5D6D7E,stroke-width:1px
    style BUS_PERIPH fill:#F4F6F7,stroke:#5D6D7E,stroke-width:1px
    style INSTR_ROM fill:#F4F6F7,stroke:#5D6D7E,stroke-width:1px